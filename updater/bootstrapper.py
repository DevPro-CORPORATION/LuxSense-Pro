"""
LuxSense Pro — Standalone Updater Bootstrapper
Replaces the installed application safely, handles Windows file locking,
creates backups, and executes automatic rollback if installation fails.
"""

import os
import sys
import time
import shutil
import logging
import argparse
import subprocess
from pathlib import Path

# Setup logging in user temp directory
log_file = Path(os.environ.get("TEMP", ".")) / "luxsense_pro_updater.log"
logging.basicConfig(
    filename=str(log_file),
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

def wait_for_process_exit(pid: int, timeout_sec: int = 15) -> bool:
    """Waits for the specified PID to terminate to avoid Windows file sharing violations."""
    logging.info(f"Waiting for process {pid} to terminate...")
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        try:
            if sys.platform == "win32":
                import ctypes
                PROCESS_QUERY_INFORMATION = 0x0400
                SYNCHRONIZE = 0x00100000
                h_proc = ctypes.windll.kernel32.OpenProcess(SYNCHRONIZE | PROCESS_QUERY_INFORMATION, False, pid)
                if not h_proc:
                    logging.info(f"Process {pid} exited.")
                    return True
                ctypes.windll.kernel32.CloseHandle(h_proc)
            else:
                os.kill(pid, 0)
        except OSError:
            logging.info(f"Process {pid} has terminated.")
            return True
        time.sleep(0.5)

    logging.warning(f"Process {pid} did not exit within {timeout_sec}s.")
    return False

def terminate_stale_processes(target_dir: Path):
    """Forcefully terminates any lingering LuxSense Pro or QtWebEngine instances to release file locks."""
    if sys.platform == "win32":
        try:
            # Forcefully terminate any remaining LuxSensePro.exe or child QtWebEngineProcess
            subprocess.run(
                ["taskkill", "/F", "/IM", "LuxSensePro.exe", "/T"],
                capture_output=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            subprocess.run(
                ["taskkill", "/F", "/IM", "QtWebEngineProcess.exe", "/T"],
                capture_output=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
        except Exception as e:
            logging.warning(f"Note during process cleanup: {e}")
        time.sleep(1.0)

def ensure_file_unlocked(file_path: Path, timeout_sec: int = 6) -> bool:
    """Ensure target executable is writable and not locked by Windows file sharing."""
    if not file_path.exists():
        return True
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        try:
            with open(file_path, "a+b") as f:
                pass
            return True
        except (PermissionError, OSError):
            time.sleep(0.5)
    return False

def create_backup(target_dir: Path) -> Path:
    """Creates a timestamped backup directory for rollback safety."""
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    backup_dir = target_dir.parent / f"{target_dir.name}_backup_{timestamp}"
    logging.info(f"Creating backup from {target_dir} to {backup_dir}")
    if backup_dir.exists():
        shutil.rmtree(backup_dir, ignore_errors=True)
    shutil.copytree(target_dir, backup_dir, dirs_exist_ok=True)
    return backup_dir

def rollback(backup_dir: Path, target_dir: Path):
    """Restores application from backup directory."""
    logging.error(f"Executing rollback from {backup_dir} to {target_dir}")
    try:
        if target_dir.exists():
            shutil.rmtree(target_dir, ignore_errors=True)
        shutil.copytree(backup_dir, target_dir, dirs_exist_ok=True)
        logging.info("Rollback completed successfully.")
    except Exception as e:
        logging.critical(f"FATAL: Rollback failed: {e}")

def run_installer(installer_path: Path, silent: bool = True, target_dir: Optional[Path] = None) -> int:
    """Executes the verified installer binary, forcing installation to target directory."""
    logging.info(f"Running installer: {installer_path} (silent={silent}, target_dir={target_dir})")
    cmd = [str(installer_path)]
    if silent:
        # Inno Setup standard silent flags
        cmd.extend(["/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART", "/SP-"])
    if target_dir:
        cmd.append(f"/DIR={str(target_dir)}")

    proc = subprocess.run(cmd, capture_output=True, text=True)
    logging.info(f"Installer finished with exit code: {proc.returncode}")
    if proc.returncode != 0:
        logging.error(f"Installer stderr: {proc.stderr}")
    return proc.returncode

def main():
    parser = argparse.ArgumentParser(description="LuxSense Pro Updater Bootstrapper")
    parser.add_argument("--installer", required=True, help="Path to verified installer binary")
    parser.add_argument("--target-exe", required=True, help="Path to installed application executable")
    parser.add_argument("--wait-pid", type=int, default=0, help="PID of running app to wait for")
    parser.add_argument("--silent", action="store_true", help="Run installer silently")
    args = parser.parse_args()

    installer_path = Path(args.installer).resolve()
    target_exe = Path(args.target_exe).resolve()
    target_dir = target_exe.parent

    logging.info(f"Starting updater bootstrapper. Target: {target_exe}")

    # 1. Wait for parent process to exit
    if args.wait_pid > 0:
        wait_for_process_exit(args.wait_pid, timeout_sec=8)

    # 2. Terminate any lingering background processes that might lock files
    terminate_stale_processes(target_dir)

    # 3. Ensure target executable file lock is released
    if not ensure_file_unlocked(target_exe):
        logging.warning("Target executable still reported locked; forcing process cleanup...")
        terminate_stale_processes(target_dir)

    # 4. Create backup of current installation
    backup_dir = None
    if target_dir.exists() and any(target_dir.iterdir()):
        try:
            backup_dir = create_backup(target_dir)
        except Exception as e:
            logging.warning(f"Could not create full backup ({e}), proceeding with cautious update.")

    # 5. Record initial modification time to verify replacement
    initial_mtime = target_exe.stat().st_mtime if target_exe.exists() else 0

    # 6. Execute installer with target directory explicitly passed
    exit_code = run_installer(installer_path, silent=args.silent, target_dir=target_dir)

    # 7. Check result and perform rollback if needed
    if exit_code != 0 or not target_exe.exists():
        logging.error(f"Installation failed with code {exit_code}. Initiating recovery...")
        if backup_dir and backup_dir.exists():
            rollback(backup_dir, target_dir)
            logging.info("Recovery restored previous version.")
            if target_exe.exists():
                subprocess.Popen([str(target_exe)])
        sys.exit(exit_code or 1)

    # 8. Check if default Inno Setup path was updated if target_dir was custom
    default_inno_path = Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "DevPro" / "LuxSense Pro" / "LuxSensePro.exe"
    if default_inno_path.exists() and default_inno_path != target_exe:
        if default_inno_path.stat().st_mtime > initial_mtime:
            logging.info(f"Detected updated binary in default path ({default_inno_path}), syncing to {target_dir}...")
            try:
                shutil.copy2(default_inno_path, target_exe)
            except Exception as e:
                logging.warning(f"Could not copy from default path: {e}")

    # 9. Success! Clean up backup and relaunch updated application
    logging.info("Update installed successfully. Cleaning up temporary backup...")
    if backup_dir and backup_dir.exists():
        try:
            shutil.rmtree(backup_dir, ignore_errors=True)
        except Exception:
            pass

    # Clean up downloaded installer
    try:
        installer_path.unlink(missing_ok=True)
    except Exception:
        pass

    # Relaunch application
    logging.info(f"Relaunching updated application: {target_exe}")
    subprocess.Popen([str(target_exe)])
    sys.exit(0)

if __name__ == "__main__":
    main()

