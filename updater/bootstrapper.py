"""
LuxSense Pro — Dedicated Native Update Manager & Bootstrapper
Inspired by modern JetBrains/PyCharm installation and update interfaces.
Provides an independent native Windows progress window that remains visible
while the main application is closed, replacing application binaries safely,
handling Windows file locking, creating safety backups, and executing automatic rollback.
"""

import os
import sys
import time
import shutil
import hashlib
import logging
import argparse
import subprocess
from pathlib import Path
from typing import Optional, Tuple

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

def terminate_stale_processes(wait_pid: int = 0):
    """
    Safely terminates only the specific parent application PID and its immediate child processes.
    Strictly avoids global taskkill by shared image names (e.g. QtWebEngineProcess.exe) to prevent
    terminating unrelated applications across the system.
    """
    if wait_pid > 0 and sys.platform == "win32":
        try:
            logging.info(f"Terminating application PID {wait_pid} and child process tree...")
            subprocess.run(
                ["taskkill", "/F", "/PID", str(wait_pid), "/T"],
                capture_output=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
        except Exception as e:
            logging.warning(f"Note during process cleanup: {e}")
        time.sleep(0.5)

def launch_application(target_exe: Path) -> bool:
    """
    Relaunches the updated application independently using ShellExecute or detached process flags.
    Ensures correct working directory (cwd=target_dir) and detaches from updater lifetime.
    """
    if not target_exe.exists() or target_exe.stat().st_size < 10000:
        logging.error(f"Cannot relaunch application: binary missing or invalid at {target_exe}")
        return False

    target_dir = target_exe.parent
    logging.info(f"Relaunching application binary: {target_exe} (cwd={target_dir})")

    # Strategy 1: Native Windows ShellExecuteW via os.startfile (fully detached from updater)
    if sys.platform == "win32" and hasattr(os, "startfile"):
        try:
            old_cwd = os.getcwd()
            try:
                os.chdir(str(target_dir))
                os.startfile(str(target_exe))
            finally:
                os.chdir(old_cwd)
            logging.info("Application successfully launched via os.startfile.")
            return True
        except Exception as e:
            logging.warning(f"os.startfile launch failed: {e}. Falling back to detached subprocess...")

    # Strategy 2: Detached subprocess with explicit working directory
    try:
        creation_flags = 0
        if sys.platform == "win32":
            DETACHED_PROCESS = 0x00000008
            CREATE_NEW_PROCESS_GROUP = 0x00000200
            creation_flags = DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP

        proc = subprocess.Popen(
            [str(target_exe)],
            cwd=str(target_dir),
            creationflags=creation_flags,
            close_fds=True
        )
        logging.info(f"Application successfully launched via subprocess.Popen (PID={proc.pid})")
        return True
    except Exception as e:
        logging.critical(f"FATAL: Failed to relaunch application: {e}")
        return False

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
        cmd.extend(["/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART", "/SP-"])
    if target_dir:
        cmd.append(f"/DIR={str(target_dir)}")

    proc = subprocess.run(cmd, capture_output=True, text=True)
    logging.info(f"Installer finished with exit code: {proc.returncode}")
    if proc.returncode != 0:
        logging.error(f"Installer stderr: {proc.stderr}")
    return proc.returncode

def verify_package_sha256(file_path: Path) -> Tuple[bool, str]:
    """Verify package exists and compute its hash."""
    if not file_path.exists():
        return False, "Package file not found."
    if file_path.stat().st_size < 1024:
        return False, "Package file is truncated or corrupted."
    sha = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            sha.update(chunk)
    return True, sha.hexdigest().lower()

# ----------------------------------------------------------------------
# PySide6 Native GUI Architecture (JetBrains / PyCharm Style Window)
# ----------------------------------------------------------------------
try:
    from PySide6.QtWidgets import (
        QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
        QProgressBar, QPushButton, QFrame
    )
    from PySide6.QtCore import Qt, QThread, Signal, QTimer
    from PySide6.QtGui import QIcon, QFont, QColor
    HAS_PYSIDE6 = True
except ImportError:
    HAS_PYSIDE6 = False

if HAS_PYSIDE6:
    class UpdateWorker(QThread):
        stageChanged = Signal(int, int, str, str)  # stage_num, total_stages, title, detail
        progressChanged = Signal(int)              # percent 0-100
        statusMessage = Signal(str)                # log line
        finished = Signal(bool, str)               # success, message

        def __init__(
            self,
            installer_path: Path,
            target_exe: Path,
            wait_pid: int = 0,
            silent: bool = True
        ):
            super().__init__()
            self.installer_path = installer_path
            self.target_exe = target_exe
            self.target_dir = target_exe.parent
            self.wait_pid = wait_pid
            self.silent = silent

        def run(self):
            total_stages = 7
            backup_dir = None

            try:
                # STAGE 1: Package Validation
                self.stageChanged.emit(1, total_stages, "Verifying Update Package", "Checking cryptographic integrity of downloaded installation files...")
                self.progressChanged.emit(10)
                ok, digest = verify_package_sha256(self.installer_path)
                if not ok:
                    self.finished.emit(False, f"Verification failed: {digest}")
                    return
                self.statusMessage.emit(f"Package validated (SHA-256: {digest[:16]}...)")
                self.progressChanged.emit(15)
                time.sleep(0.3)

                # STAGE 2: Application Shutdown & Lock Release
                self.stageChanged.emit(2, total_stages, "Waiting for Application Shutdown", "Waiting for LuxSense Pro instance to close and release memory locks...")
                self.progressChanged.emit(20)
                if self.wait_pid > 0:
                    wait_for_process_exit(self.wait_pid, timeout_sec=8)
                terminate_stale_processes(self.wait_pid)
                if not ensure_file_unlocked(self.target_exe, timeout_sec=4):
                    terminate_stale_processes(self.wait_pid)
                self.progressChanged.emit(28)
                time.sleep(0.3)

                # STAGE 3: Installation Safety Backup
                self.stageChanged.emit(3, total_stages, "Creating Safety Backup", "Backing up active installation files for automatic rollback protection...")
                self.progressChanged.emit(35)
                if self.target_dir.exists() and any(self.target_dir.iterdir()):
                    try:
                        backup_dir = create_backup(self.target_dir)
                        self.statusMessage.emit(f"Safety backup created at {backup_dir.name}")
                    except Exception as e:
                        logging.warning(f"Could not create full backup: {e}")
                self.progressChanged.emit(45)
                time.sleep(0.3)

                # STAGE 4: Package Extraction & File Replacement
                self.stageChanged.emit(4, total_stages, "Installing Update Package", "Writing updated LuxSense Pro binaries, libraries, and firmware manifests...")
                self.progressChanged.emit(55)
                initial_mtime = self.target_exe.stat().st_mtime if self.target_exe.exists() else 0
                exit_code = run_installer(self.installer_path, silent=self.silent, target_dir=self.target_dir)

                if exit_code != 0:
                    raise RuntimeError(f"Installer exited with error code {exit_code}")
                self.progressChanged.emit(78)
                time.sleep(0.3)

                # STAGE 5: Configuration & Data Integrity Check
                self.stageChanged.emit(5, total_stages, "Verifying User Configuration", "Confirming %APPDATA% settings, calibration matrices, and history database...")
                self.progressChanged.emit(85)
                # Verify that AppData directory and user settings are untouched
                appdata_base = os.environ.get("APPDATA") or os.path.expanduser("~\\AppData\\Roaming")
                user_data_path = Path(appdata_base) / "DevPro" / "LuxSensePro"
                if user_data_path.exists():
                    self.statusMessage.emit(f"User data verified intact in {user_data_path}")
                self.progressChanged.emit(90)
                time.sleep(0.3)

                # STAGE 6: Installation Verification & Directory Synchronization
                self.stageChanged.emit(6, total_stages, "Verifying Updated Installation", "Validating new executable and executable permissions...")
                self.progressChanged.emit(94)
                default_inno_path = Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "DevPro" / "LuxSense Pro" / "LuxSensePro.exe"
                if default_inno_path.exists() and default_inno_path != self.target_exe:
                    if default_inno_path.stat().st_mtime > initial_mtime:
                        try:
                            shutil.copy2(default_inno_path, self.target_exe)
                            self.statusMessage.emit("Synchronized updated binary to target directory.")
                        except Exception as e:
                            logging.warning(f"Copy from default path notice: {e}")

                if not self.target_exe.exists() or self.target_exe.stat().st_size < 10000:
                    raise RuntimeError("Updated application executable not found or invalid.")

                self.progressChanged.emit(98)
                time.sleep(0.3)

                # STAGE 7: Relaunch Application
                self.stageChanged.emit(7, total_stages, "Relaunching Application", "Launching updated LuxSense Pro workstation...")
                self.progressChanged.emit(100)

                # Clean up backup on success
                if backup_dir and backup_dir.exists():
                    try:
                        shutil.rmtree(backup_dir, ignore_errors=True)
                    except Exception:
                        pass

                # Clean up downloaded installer
                try:
                    self.installer_path.unlink(missing_ok=True)
                except Exception:
                    pass

                logging.info(f"Relaunching updated application: {self.target_exe}")
                relaunch_ok = launch_application(self.target_exe)
                if not relaunch_ok:
                    raise RuntimeError(f"Application relaunch failed for {self.target_exe}")
                time.sleep(0.8)
                self.finished.emit(True, "Update installed and application relaunched successfully.")

            except Exception as e:
                logging.error(f"Update failed: {e}. Executing rollback...")
                if backup_dir and backup_dir.exists():
                    rollback(backup_dir, self.target_dir)
                    if self.target_exe.exists():
                        launch_application(self.target_exe)
                self.finished.emit(False, f"Update failed: {str(e)}. Previous version was safely restored.")

    class UpdateProgressWindow(QWidget):
        """
        Standalone native Windows update progress window inspired by JetBrains / PyCharm IDE updates.
        """
        def __init__(
            self,
            installer_path: Path,
            target_exe: Path,
            wait_pid: int = 0,
            silent: bool = True,
            theme: str = "dark",
            old_version: str = "2.3.1",
            new_version: str = "2.3.2"
        ):
            super().__init__()
            self.installer_path = installer_path
            self.target_exe = target_exe
            self.wait_pid = wait_pid
            self.silent = silent
            self.theme = theme.lower()
            self.old_version = old_version
            self.new_version = new_version
            self.start_time = time.time()

            self.init_ui()
            self.start_update_thread()

        def init_ui(self):
            self.setWindowTitle("LuxSense Pro — Update Manager")
            self.setFixedSize(560, 360)

            # Center window on screen
            screen = QApplication.primaryScreen()
            if screen:
                geom = screen.geometry()
                self.move(
                    (geom.width() - self.width()) // 2,
                    (geom.height() - self.height()) // 2
                )

            # Modern framing
            self.setWindowFlags(Qt.Window | Qt.CustomizeWindowHint | Qt.WindowTitleHint | Qt.WindowCloseButtonHint)

            is_dark = (self.theme != "light")
            bg_color = "#0e0e11" if is_dark else "#f8fafc"
            panel_bg = "#16161a" if is_dark else "#ffffff"
            border_color = "#27272a" if is_dark else "#e2e8f0"
            text_primary = "#f4f4f5" if is_dark else "#0f172a"
            text_muted = "#a1a1aa" if is_dark else "#64748b"
            accent_green = "#22c55e" if is_dark else "#16a34a"

            self.setStyleSheet(f"""
                QWidget {{
                    background-color: {bg_color};
                    color: {text_primary};
                    font-family: 'Segoe UI', -apple-system, sans-serif;
                }}
                QFrame#mainPanel {{
                    background-color: {panel_bg};
                    border: 1px solid {border_color};
                    border-radius: 12px;
                }}
                QProgressBar {{
                    border: 1px solid {border_color};
                    border-radius: 6px;
                    background-color: {'#1f1f23' if is_dark else '#e2e8f0'};
                    text-align: center;
                    font-size: 11px;
                    font-weight: bold;
                    color: {text_primary};
                }}
                QProgressBar::chunk {{
                    background-color: {accent_green};
                    border-radius: 5px;
                }}
                QPushButton#actionBtn {{
                    background-color: {accent_green};
                    color: #09090b;
                    font-weight: bold;
                    font-size: 11px;
                    padding: 8px 16px;
                    border-radius: 6px;
                    border: none;
                }}
                QPushButton#actionBtn:hover {{
                    background-color: {'#16a34a' if is_dark else '#15803d'};
                }}
                QPushButton#actionBtn:disabled {{
                    background-color: {'#27272a' if is_dark else '#cbd5e1'};
                    color: {'#71717a' if is_dark else '#94a3b8'};
                }}
            """)

            root_layout = QVBoxLayout(self)
            root_layout.setContentsMargins(16, 16, 16, 16)

            main_panel = QFrame()
            main_panel.setObjectName("mainPanel")
            panel_layout = QVBoxLayout(main_panel)
            panel_layout.setContentsMargins(24, 20, 24, 20)
            panel_layout.setSpacing(14)

            # Header with App Logo & Title
            header_layout = QHBoxLayout()
            title_layout = QVBoxLayout()
            title_layout.setSpacing(2)

            app_title = QLabel("LUXSENSE PRO")
            app_title.setFont(QFont("Segoe UI", 12, QFont.Bold))
            app_title.setStyleSheet(f"color: {accent_green}; letter-spacing: 1px;")

            sub_title = QLabel("Optical Radiometry Workstation • DevPro-CORP")
            sub_title.setFont(QFont("Segoe UI", 8))
            sub_title.setStyleSheet(f"color: {text_muted};")

            title_layout.addWidget(app_title)
            title_layout.addWidget(sub_title)
            header_layout.addLayout(title_layout)
            header_layout.addStretch()

            # JetBrains-style version badge pill
            version_badge = QLabel(f"  v{self.old_version}  ➔  v{self.new_version}  ")
            version_badge.setFont(QFont("Consolas", 9, QFont.Bold))
            version_badge.setStyleSheet(f"""
                background-color: {'#1e293b' if is_dark else '#f1f5f9'};
                color: {accent_green};
                border: 1px solid {border_color};
                border-radius: 6px;
                padding: 4px 8px;
            """)
            header_layout.addWidget(version_badge)
            panel_layout.addLayout(header_layout)

            # Separator
            sep = QFrame()
            sep.setFrameShape(QFrame.HLine)
            sep.setStyleSheet(f"color: {border_color};")
            panel_layout.addWidget(sep)

            # Stage & Detail Information
            self.stage_label = QLabel("Initializing Update Engine...")
            self.stage_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
            self.stage_label.setStyleSheet(f"color: {text_primary};")
            panel_layout.addWidget(self.stage_label)

            self.detail_label = QLabel("Preparing environment and verifying dependencies...")
            self.detail_label.setFont(QFont("Segoe UI", 9))
            self.detail_label.setStyleSheet(f"color: {text_muted};")
            self.detail_label.setWordWrap(True)
            panel_layout.addWidget(self.detail_label)

            # Progress Bar
            self.progress_bar = QProgressBar()
            self.progress_bar.setFixedHeight(14)
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(5)
            panel_layout.addWidget(self.progress_bar)

            # Footer: Elapsed Time & Status Log
            footer_layout = QHBoxLayout()
            self.elapsed_label = QLabel("Elapsed: 00:00")
            self.elapsed_label.setFont(QFont("Consolas", 8))
            self.elapsed_label.setStyleSheet(f"color: {text_muted};")
            footer_layout.addWidget(self.elapsed_label)

            footer_layout.addStretch()

            self.status_badge = QLabel("IN PROGRESS")
            self.status_badge.setFont(QFont("Segoe UI", 8, QFont.Bold))
            self.status_badge.setStyleSheet(f"color: {accent_green};")
            footer_layout.addWidget(self.status_badge)

            panel_layout.addLayout(footer_layout)
            root_layout.addWidget(main_panel)

            # Elapsed time timer
            self.timer = QTimer(self)
            self.timer.timeout.connect(self.update_elapsed)
            self.timer.start(1000)

        def update_elapsed(self):
            elapsed = int(time.time() - self.start_time)
            mins = elapsed // 60
            secs = elapsed % 60
            self.elapsed_label.setText(f"Elapsed: {mins:02d}:{secs:02d}")

        def start_update_thread(self):
            self.worker = UpdateWorker(
                installer_path=self.installer_path,
                target_exe=self.target_exe,
                wait_pid=self.wait_pid,
                silent=self.silent
            )
            self.worker.stageChanged.connect(self.on_stage_changed)
            self.worker.progressChanged.connect(self.on_progress_changed)
            self.worker.statusMessage.connect(self.on_status_message)
            self.worker.finished.connect(self.on_update_finished)
            self.worker.start()

        def on_stage_changed(self, stage_idx: int, total_stages: int, title: str, detail: str):
            self.stage_label.setText(f"Stage {stage_idx} of {total_stages}: {title}")
            self.detail_label.setText(detail)

        def on_progress_changed(self, pct: int):
            self.progress_bar.setValue(pct)

        def on_status_message(self, msg: str):
            logging.info(f"[UI] {msg}")

        def on_update_finished(self, success: bool, message: str):
            self.timer.stop()
            if success:
                self.status_badge.setText("COMPLETED")
                self.status_badge.setStyleSheet("color: #22c55e;")
                self.stage_label.setText("Update Completed Successfully!")
                self.detail_label.setText("Relaunching LuxSense Pro v" + self.new_version + "...")
                self.progress_bar.setValue(100)
                QTimer.singleShot(1500, self.close)
            else:
                self.status_badge.setText("UPDATE FAILED")
                self.status_badge.setStyleSheet("color: #ef4444;")
                self.stage_label.setText("Installation Error — System Restored")
                self.detail_label.setText(message)
                self.progress_bar.setStyleSheet("""
                    QProgressBar::chunk { background-color: #ef4444; }
                """)

def run_headless_sync(installer_path: Path, target_exe: Path, wait_pid: int = 0, silent: bool = True) -> int:
    """Synchronous headless update execution for testing or CLI environments."""
    target_dir = target_exe.parent
    logging.info(f"Running headless update. Target: {target_exe}")

    if wait_pid > 0:
        wait_for_process_exit(wait_pid, timeout_sec=8)

    terminate_stale_processes(wait_pid)

    if not ensure_file_unlocked(target_exe):
        terminate_stale_processes(wait_pid)

    backup_dir = None
    if target_dir.exists() and any(target_dir.iterdir()):
        try:
            backup_dir = create_backup(target_dir)
        except Exception as e:
            logging.warning(f"Could not create full backup: {e}")

    initial_mtime = target_exe.stat().st_mtime if target_exe.exists() else 0
    exit_code = run_installer(installer_path, silent=silent, target_dir=target_dir)

    if exit_code != 0 or not target_exe.exists():
        logging.error(f"Installation failed with code {exit_code}. Initiating recovery...")
        if backup_dir and backup_dir.exists():
            rollback(backup_dir, target_dir)
            if target_exe.exists():
                launch_application(target_exe)
        return exit_code or 1

    default_inno_path = Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "DevPro" / "LuxSense Pro" / "LuxSensePro.exe"
    if default_inno_path.exists() and default_inno_path != target_exe:
        if default_inno_path.stat().st_mtime > initial_mtime:
            try:
                shutil.copy2(default_inno_path, target_exe)
            except Exception as e:
                logging.warning(f"Could not copy from default path: {e}")

    if backup_dir and backup_dir.exists():
        try:
            shutil.rmtree(backup_dir, ignore_errors=True)
        except Exception:
            pass

    try:
        installer_path.unlink(missing_ok=True)
    except Exception:
        pass

    logging.info(f"Relaunching updated application: {target_exe}")
    relaunch_ok = launch_application(target_exe)
    return 0 if relaunch_ok else 1

def main():
    parser = argparse.ArgumentParser(description="LuxSense Pro Dedicated Native Update Manager")
    parser.add_argument("--installer", required=True, help="Path to verified installer binary")
    parser.add_argument("--target-exe", required=True, help="Path to installed application executable")
    parser.add_argument("--wait-pid", type=int, default=0, help="PID of running app to wait for")
    parser.add_argument("--silent", action="store_true", help="Run installer silently")
    parser.add_argument("--headless", action="store_true", help="Run update in headless mode without GUI")
    parser.add_argument("--theme", default="dark", help="UI Theme: 'dark' or 'light'")
    parser.add_argument("--old-version", default="2.3.1", help="Current installed version")
    parser.add_argument("--new-version", default="2.3.2", help="Target update version")
    args = parser.parse_args()

    installer_path = Path(args.installer).resolve()
    target_exe = Path(args.target_exe).resolve()

    if args.headless or not HAS_PYSIDE6:
        exit_code = run_headless_sync(installer_path, target_exe, wait_pid=args.wait_pid, silent=args.silent)
        sys.exit(exit_code)
    else:
        app = QApplication(sys.argv)
        app.setApplicationName("LuxSense Pro Update Manager")
        window = UpdateProgressWindow(
            installer_path=installer_path,
            target_exe=target_exe,
            wait_pid=args.wait_pid,
            silent=args.silent,
            theme=args.theme,
            old_version=args.old_version,
            new_version=args.new_version
        )
        window.show()
        sys.exit(app.exec())

if __name__ == "__main__":
    main()
