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

# Setup logging
log_file = Path(os.environ.get("TEMP", ".")) / "luxsense_pro_updater.log"
logging.basicConfig(
    filename=str(log_file),
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

def wait_for_process_exit(pid: int, timeout_sec: int = 15) -> bool:
    """Waits for the specified PID to terminate to avoid Windows sharing violations."""
    logging.info(f"Waiting for process {pid} to terminate...")
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        try:
            # On Windows, OpenProcess check
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

def create_backup(target_dir: Path) -> Path:
    """Creates a timestamped backup directory for rollback safety."""
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    backup_dir = target_dir.parent / f"{target_dir.name}_backup_{timestamp}"
    logging.info(f"Creating backup from {target_dir} to {backup_dir}")
    if backup_dir.exists():
        shutil.rmtree(backup_dir, ignore_errors=True)
    shutil.copytree(target_dir, backup_dir)
    return backup_dir

def rollback(backup_dir: Path, target_dir: Path):
    """Restores application from backup directory."""
    logging.error(f"Executing rollback from {backup_dir} to {target_dir}")
    try:
        if target_dir.exists():
            shutil.rmtree(target_dir, ignore_errors=True)
        shutil.copytree(backup_dir, target_dir)
        logging.info("Rollback completed successfully.")
    except Exception as e:
        logging.critical(f"FATAL: Rollback failed: {e}")

def run_installer(installer_path: Path, silent: bool = True) -> int:
    """Executes the verified installer binary."""
    logging.info(f"Running installer: {installer_path} (silent={silent})")
    cmd = [str(installer_path)]
    if silent:
        # Inno Setup standard silent flags
        cmd.extend(["/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART", "/SP-"])
    
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
        if not wait_for_process_exit(args.wait_pid):
            logging.error(f"Target process {args.wait_pid} is still active. Aborting update.")
            sys.exit(1)

    time.sleep(1.0)

    # 2. Create backup of current installation
    backup_dir = None
    if target_dir.exists() and any(target_dir.iterdir()):
        try:
            backup_dir = create_backup(target_dir)
        except Exception as e:
            logging.warning(f"Could not create full backup ({e}), proceeding with cautious update.")

    # 3. Execute installer
    exit_code = run_installer(installer_path, silent=args.silent)

    # 4. Check result and perform rollback if needed
    if exit_code != 0 or not target_exe.exists():
        logging.error(f"Installation failed with code {exit_code}. Initiating recovery...")
        if backup_dir and backup_dir.exists():
            rollback(backup_dir, target_dir)
            logging.info("Recovery restored previous version.")
            # Relaunch restored version
            if target_exe.exists():
                subprocess.Popen([str(target_exe)])
        sys.exit(exit_code or 1)

    # 5. Success! Clean up backup and relaunch updated application
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
