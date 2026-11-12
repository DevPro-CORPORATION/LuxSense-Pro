"""
LuxSense Pro — Main Window UI
Central desktop window with professional scientific styling, multi-tab layout,
integrated serial worker, and automatic update manager.
"""

import sys
import webbrowser
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QApplication, QFrame, QLabel, QMainWindow, QTabWidget,
    QVBoxLayout, QWidget, QHBoxLayout, QMessageBox
)

from app.core.config import (
    APP_NAME,
    APP_VERSION,
    ORG_NAME,
    WEBSITE_URL,
    GITHUB_REPO_URL,
    UserSettings
)
from app.core.serial_worker import SerialWorker
from app.updater.update_manager import UpdateManager
from app.ui.monitor_tab import MonitorTab
from app.ui.analytics_tab import AnalyticsTab
from app.ui.calibration_tab import CalibrationTab
from app.ui.settings_tab import SettingsTab
from app.ui.update_dialog import UpdateDialog

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = UserSettings.load()
        self.setWindowTitle(f"{APP_NAME} — v{APP_VERSION} [{ORG_NAME}]")
        self.resize(840, 580)
        self.setMinimumSize(740, 500)
        self._apply_theme()

        self._init_ui()
        self._init_updater()
        self._init_serial()

    def _apply_theme(self):
        self.setStyleSheet("""
            QMainWindow { background: #121316; }
            QWidget { color: #DFE1E5; font-family: 'Segoe UI', sans-serif; }
            QTabWidget::pane {
                border: 1px solid #2B2F38;
                background: #181A1D;
                border-radius: 8px;
            }
            QTabBar::tab {
                background: #121316; color: #8D929B;
                padding: 10px 22px; font-size: 13px; font-weight: 600;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: #181A1D; color: #FFFFFF;
                border-bottom: 2px solid #21D789;
            }
            QPushButton {
                background: #252830;
                color: #FFFFFF;
                border: 1px solid #363B47;
                border-radius: 6px;
                padding: 6px 14px;
                font-weight: 600;
            }
            QPushButton:hover { background: #323742; }
            QPushButton#primaryBtn {
                background: #21D789;
                color: #0E1A14;
                border: 1px solid #1EB976;
            }
            QPushButton#primaryBtn:hover { background: #28E895; }
            QComboBox {
                background: #1E2126;
                border: 1px solid #363B47;
                border-radius: 5px;
                padding: 5px 10px;
                color: #DFE1E5;
            }
            QCheckBox { spacing: 8px; color: #C5CBD5; }
            QCheckBox::indicator { width: 16px; height: 16px; }
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

        subtitle = QLabel("High-Precision Optical Radiometry & Sensor Analytics • DevPro-CORP")
        subtitle.setStyleSheet("color: #7E8590; font-size: 11px;")
        title_box.addWidget(app_title)
        title_box.addWidget(subtitle)

        top.addLayout(title_box)
        top.addStretch()

        ver_badge = QLabel(f"v{APP_VERSION}")
        ver_badge.setStyleSheet("""
            background: #1E2522;
            color: #21D789;
            font-size: 11px;
            font-weight: 700;
            padding: 4px 10px;
            border: 1px solid #28543E;
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
        self.tabs.addTab(self.settings_tab, "Settings")
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
        self.settings_tab.check_updates_requested.connect(self._on_manual_check_updates)

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
            "Features automatic GitHub Releases integration, SHA-256 binary verification, "
            "Windows Authenticode publisher validation, safe rollback updater bootstrapper, "
            "and persistent storage in standard Windows AppData."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #A7ABB3; font-size: 13px; line-height: 1.5;")

        owner = QLabel(
            "Product Ownership: DevPro-CORP (DevPro Corporation)\n"
            "Architecture & Lead Systems: M Somasundaram\n"
            "Website: https://devpro-corporation.github.io/luxsense-pro/\n"
            "Repository: https://github.com/DevPro-CORPORATION/luxsense-pro"
        )
        owner.setStyleSheet("color: #21D789; font-size: 12px; font-family: 'Consolas', monospace;")

        btn_row = QHBoxLayout()
        web_btn = QPushButton("Visit Product Website")
        web_btn.clicked.connect(lambda: webbrowser.open(WEBSITE_URL))

        repo_btn = QPushButton("View GitHub Repository")
        repo_btn.clicked.connect(lambda: webbrowser.open(GITHUB_REPO_URL))

        btn_row.addWidget(web_btn)
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
        self.updater = UpdateManager()
        self.updater.update_available.connect(self._on_update_available)
        self.updater.update_not_available.connect(self._on_update_not_available)
        self.updater.update_error.connect(self._on_update_error)
        self.updater.download_progress.connect(self._on_download_progress)
        self.updater.ready_to_install.connect(self._on_ready_to_install)
        self.updater.verification_failed.connect(self._on_verification_failed)

        self._current_update_dialog = None

        # Check for updates on startup if enabled
        if self.settings.auto_check_updates:
            QTimer.singleShot(2500, lambda: self.updater.check_for_updates(manual=False))

    def _on_manual_check_updates(self):
        self.updater.clear_postponed()
        self.updater.check_for_updates(manual=True)

    def _on_update_available(self, release_data: dict):
        self.settings_tab.set_update_status(f"Update available: {release_data.get('tag_name')}", "#21D789")
        dialog = UpdateDialog(release_data, self)
        self._current_update_dialog = dialog
        dialog.install_confirmed.connect(self._on_user_confirmed_update)
        dialog.postponed.connect(self.updater.postpone_update)
        dialog.show()

    def _on_update_not_available(self, msg: str):
        self.settings_tab.set_update_status(msg, "#8D929B")

    def _on_update_error(self, err_msg: str):
        self.settings_tab.set_update_status(f"Check failed: {err_msg}", "#E06C75")

    def _on_user_confirmed_update(self, release_data: dict):
        if self._current_update_dialog:
            self._current_update_dialog.status_label.setVisible(True)
            self._current_update_dialog.status_label.setText("Initiating verified download...")
        self.updater.start_download(release_data)

    def _on_download_progress(self, downloaded: int, total: int, percent: float):
        if self._current_update_dialog:
            self._current_update_dialog.set_download_progress(downloaded, total, percent)

    def _on_ready_to_install(self, installer_path):
        if self._current_update_dialog:
            self._current_update_dialog.accept()

        reply = QMessageBox.question(
            self,
            "Update Ready to Install",
            "The update has been downloaded and verified successfully (SHA-256 and digital signature valid).\n\n"
            "LuxSense Pro will now restart and hand over to the updater bootstrapper to apply the update.\n"
            "Your user settings, calibration profiles, and measurement history will be preserved.\n\n"
            "Proceed with installation now?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.worker.stop()
            self.updater.launch_installer(installer_path)

    def _on_verification_failed(self, error_message: str):
        if self._current_update_dialog:
            self._current_update_dialog.reject()
        QMessageBox.critical(self, "Security Verification Failed", error_message)

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

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())
