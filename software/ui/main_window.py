"""
LuxSense Pro — Main Window UI
Central desktop window with professional scientific styling, multi-tab layout,
integrated serial worker, and GitHub-powered Update Center.
"""

import sys
import webbrowser
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QApplication, QFrame, QLabel, QMainWindow, QTabWidget,
    QVBoxLayout, QWidget, QHBoxLayout, QMessageBox
)

from software.core.config import (
    APP_NAME,
    APP_VERSION,
    ORG_NAME,
    GITHUB_REPO_URL
)
from software.core.storage import UserSettings
from software.core.serial_worker import SerialWorker
from software.ui.monitor_tab import MonitorTab
from software.ui.analytics_tab import AnalyticsTab
from software.ui.calibration_tab import CalibrationTab
from software.ui.settings_tab import SettingsTab
from updater.update_manager import UpdateManager

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = UserSettings.load()
        self.setWindowTitle(f"{APP_NAME} — v{APP_VERSION} [{ORG_NAME}]")
        self.resize(860, 600)
        self.setMinimumSize(760, 520)
        self._apply_theme()

        self._init_ui()
        self._init_updater()
        self._init_serial()

    def _apply_theme(self):
        self.setStyleSheet("""
            QMainWindow { background: #0E1013; }
            QWidget { color: #DFE1E5; font-family: 'Segoe UI', sans-serif; }
            QTabWidget::pane {
                border: 1px solid #272C37;
                background: #15181E;
                border-radius: 8px;
            }
            QTabBar::tab {
                background: #0E1013; color: #8D929B;
                padding: 10px 22px; font-size: 13px; font-weight: 600;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: #15181E; color: #FFFFFF;
                border-bottom: 2px solid #21D789;
            }
            QPushButton {
                background: #1E232B;
                color: #FFFFFF;
                border: 1px solid #323A4A;
                border-radius: 6px;
                padding: 6px 14px;
                font-weight: 600;
            }
            QPushButton:hover { background: #2A3240; }
            QPushButton#primaryBtn {
                background: #21D789;
                color: #0E1A14;
                border: 1px solid #1EB976;
            }
            QPushButton#primaryBtn:hover { background: #28E895; }
            QComboBox {
                background: #181A1D;
                border: 1px solid #323A4A;
                border-radius: 5px;
                padding: 5px 10px;
                color: #DFE1E5;
            }
            QCheckBox { spacing: 8px; color: #C5CBD5; }
            QCheckBox::indicator { width: 16px; height: 16px; }
            QProgressBar {
                background: #141618;
                border: 1px solid #2B303A;
                border-radius: 4px;
                text-align: center;
                color: white;
                font-weight: 600;
            }
            QProgressBar::chunk {
                background: #21D789;
                border-radius: 3px;
            }
        """)

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(20, 16, 20, 14)
        root.setSpacing(10)

        # Header Bar
        top = QHBoxLayout()
        title_box = QVBoxLayout()
        title_box.setSpacing(2)

        app_title = QLabel("LuxSense Pro")
        app_title.setStyleSheet("font-size: 20px; font-weight: 700; color: #FFFFFF; letter-spacing: 0.5px;")

        channel_text = f"Channel: {self.settings.update_channel.upper()}"
        subtitle = QLabel(f"Precision Optical Radiometry • {ORG_NAME} • {channel_text}")
        subtitle.setStyleSheet("color: #7E8590; font-size: 11px;")
        title_box.addWidget(app_title)
        title_box.addWidget(subtitle)

        top.addLayout(title_box)
        top.addStretch()

        ver_badge = QLabel(f"v{APP_VERSION}")
        ver_badge.setStyleSheet("""
            background: #14221A;
            color: #21D789;
            font-size: 11px;
            font-weight: 700;
            padding: 4px 12px;
            border: 1px solid #1E5037;
            border-radius: 12px;
        """)
        top.addWidget(ver_badge)
        root.addLayout(top)

        # Tabs
        self.tabs = QTabWidget()
        self.monitor_tab = MonitorTab()
        self.analytics_tab = AnalyticsTab()
        self.calibration_tab = CalibrationTab()
        self.settings_tab = SettingsTab()
        self.about_tab = self._create_about_tab()

        self.tabs.addTab(self.monitor_tab, "Live Monitor")
        self.tabs.addTab(self.analytics_tab, "Analytics & History")
        self.tabs.addTab(self.calibration_tab, "Calibration")
        self.tabs.addTab(self.settings_tab, "Settings & Update Center")
        self.tabs.addTab(self.about_tab, "About DevPro-CORP")

        root.addWidget(self.tabs, 1)

        # Status Footer
        self.status = QLabel("●  Initializing hardware subsystem...")
        self.status.setWordWrap(True)
        self.status.setStyleSheet("color: #E5C07B; font-size: 12px; font-weight: 600; padding: 4px;")
        root.addWidget(self.status)

        # Signal connections
        self.calibration_tab.calibration_updated.connect(self._on_calibration_updated)
        self.settings_tab.connection_changed.connect(self._on_connection_changed)
        self.settings_tab.check_updates_requested.connect(self._on_check_updates_requested)
        self.settings_tab.download_update_requested.connect(self._on_download_update_requested)
        self.settings_tab.install_update_requested.connect(self._on_install_update_requested)

    def _create_about_tab(self) -> QWidget:
        about = QWidget()
        l = QVBoxLayout(about)
        l.setContentsMargins(28, 24, 28, 24)
        l.setSpacing(14)

        t = QLabel("LuxSense Pro — Precision Optical Metrology")
        t.setStyleSheet("font-size: 19px; font-weight: 700; color: #FFFFFF;")

        desc = QLabel(
            "LuxSense Pro is an enterprise-grade photometric sensing application engineered "
            "by DevPro-CORP. It pairs with an Arduino Uno and the BH1750 (GY-30) digital "
            "illuminance sensor over high-speed USB serial with rolling-128 XOR encrypted telemetry.\n\n"
            "Features GitHub Releases integration (Stable and Beta update channels), SHA-256 binary verification, "
            "Windows Authenticode publisher validation, safe rollback updater bootstrapper, "
            "and persistent storage in standard Windows AppData."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #A7ABB3; font-size: 13px; line-height: 1.5;")

        owner = QLabel(
            "Product Ownership: DevPro-CORP (DevPro Corporation)\n"
            "Official Release Channel: GitHub Releases (DevPro-CORPORATION/luxsense-pro)\n"
            "Update Channels: Stable (Production) | Beta (Previews)"
        )
        owner.setStyleSheet("color: #21D789; font-size: 12px; font-family: monospace;")

        btn_row = QHBoxLayout()
        repo_btn = QPushButton("View GitHub Releases Repository")
        repo_btn.clicked.connect(lambda: webbrowser.open(GITHUB_REPO_URL))
        btn_row.addWidget(repo_btn)
        btn_row.addStretch()

        l.addWidget(t)
        l.addWidget(desc)
        l.addWidget(owner)
        l.addLayout(btn_row)
        l.addStretch()
        return about

    def _init_serial(self):
        self.worker = SerialWorker(
            port=self.settings.serial_port,
            baud=self.settings.baud_rate
        )
        self.worker.status_signal.connect(self.update_status)
        self.worker.data_signal.connect(self._on_serial_data)
        self.worker.start()

    def _init_updater(self):
        self.updater = UpdateManager(current_version=APP_VERSION)
        self.updater.update_available.connect(self._on_update_available)
        self.updater.update_not_available.connect(self._on_update_not_available)
        self.updater.update_error.connect(self._on_update_error)
        self.updater.download_progress.connect(self.settings_tab.handle_download_progress)
        self.updater.ready_to_install.connect(self._on_ready_to_install)
        self.updater.verification_failed.connect(self._on_verification_failed)

        # Automatic background check on launch if enabled
        if self.settings.auto_check_updates:
            QTimer.singleShot(2500, lambda: self.updater.check_for_updates(channel=self.settings.update_channel))

    def _on_check_updates_requested(self, channel: str):
        self.settings.update_channel = channel
        self.settings.last_update_check = import_time()
        self.settings.save()
        self.updater.check_for_updates(channel=channel)

    def _on_update_available(self, release_data: dict):
        self.settings.latest_known_version = release_data.get("tag_name", "").lstrip("v")
        self.settings.save()
        self.settings_tab.handle_update_available(release_data)

    def _on_update_not_available(self, msg: str):
        self.settings_tab.handle_up_to_date(msg)

    def _on_update_error(self, err_msg: str):
        self.settings_tab.handle_update_error(err_msg)

    def _on_download_update_requested(self, release_data: dict):
        self.updater.start_download(release_data)

    def _on_ready_to_install(self, installer_path):
        self.settings_tab.handle_ready_to_install()
        reply = QMessageBox.question(
            self,
            "Update Ready to Install",
            "The update has been downloaded and cryptographically verified (SHA-256 and digital signature valid).\n\n"
            "LuxSense Pro will now restart and hand over to the updater bootstrapper.\n"
            "Your settings, calibration profiles, and measurement history will be preserved.\n\n"
            "Proceed with installation now?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._on_install_update_requested()

    def _on_install_update_requested(self):
        self.worker.stop()
        self.updater.launch_installer()

    def _on_verification_failed(self, error_message: str):
        QMessageBox.critical(self, "Security Verification Failed", error_message)
        self.settings_tab.status_lbl.setText("Security verification failed. Corrupted or unverified file deleted.")
        self.settings_tab.status_lbl.setStyleSheet("color: #E06C75;")

    def _on_serial_data(self, raw_lux: float, cal_lux: float, packet_id: int, port: str):
        self.monitor_tab.update_reading(raw_lux, cal_lux, packet_id, port)
        if self.tabs.currentWidget() == self.analytics_tab:
            self.analytics_tab.refresh_data()

    def _on_calibration_updated(self):
        self.worker.reload_calibration()

    def _on_connection_changed(self, port: str, baud: int):
        self.worker.update_config(port, baud)

    def update_status(self, message: str, color: str):
        self.status.setText(f"●  {message}")
        self.status.setStyleSheet(f"color: {color}; font-size: 12px; font-weight: 600; padding: 4px;")

    def closeEvent(self, event):
        self.worker.stop()
        event.accept()

def import_time():
    import time
    return time.strftime("%Y-%m-%d %H:%M:%S")

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())
