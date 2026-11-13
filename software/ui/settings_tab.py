"""
LuxSense Pro — Settings Tab with Integrated In-App Update Center
Displays hardware configuration, user preferences, and a complete Update Center:
- Installed version
- Latest available version
- Update channel (Stable / Beta)
- Release notes
- Check for updates button
- Download progress
- Install update button
- Last update check
"""

import os
import sys
import serial.tools.list_ports
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QCheckBox, QPushButton, QFrame,
    QProgressBar, QMessageBox, QTextBrowser
)

from software.core.config import (
    APP_VERSION,
    DEFAULT_BAUD_RATE,
    get_app_data_dir
)
from software.core.storage import UserSettings

class SettingsTab(QWidget):
    connection_changed = pyqtSignal(str, int)
    check_updates_requested = pyqtSignal(str)   # channel: "stable" or "beta"
    download_update_requested = pyqtSignal(dict)
    install_update_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings = UserSettings.load()
        self.staged_release_data = None
        self._init_ui()

    def _init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 18, 24, 18)
        root.setSpacing(14)

        # -------------------------------------------------------------
        # 1. IN-APP UPDATE CENTER (PRIMARY SYSTEM CARD)
        # -------------------------------------------------------------
        update_card = self._create_card("UPDATE CENTER — GITHUB DISTRIBUTION CHANNEL")
        u_layout = update_card.layout()

        # Grid of Version & Channel details
        info_row = QHBoxLayout()
        info_row.setSpacing(20)

        # 1. Installed version
        c_col = QVBoxLayout()
        c_title = QLabel("INSTALLED VERSION")
        c_title.setStyleSheet("font-size: 10px; font-weight: 700; color: #8D929B;")
        self.installed_ver_lbl = QLabel(f"v{APP_VERSION}")
        self.installed_ver_lbl.setStyleSheet("font-size: 16px; font-weight: 700; color: #21D789; font-family: monospace;")
        c_col.addWidget(c_title)
        c_col.addWidget(self.installed_ver_lbl)
        info_row.addLayout(c_col)

        # 2. Latest available version
        l_col = QVBoxLayout()
        l_title = QLabel("LATEST PUBLISHED")
        l_title.setStyleSheet("font-size: 10px; font-weight: 700; color: #8D929B;")
        self.latest_ver_lbl = QLabel(f"v{self.settings.latest_known_version}")
        self.latest_ver_lbl.setStyleSheet("font-size: 16px; font-weight: 700; color: #E2E4E9; font-family: monospace;")
        l_col.addWidget(l_title)
        l_col.addWidget(self.latest_ver_lbl)
        info_row.addLayout(l_col)

        # 3. Update channel (Stable / Beta)
        ch_col = QVBoxLayout()
        ch_title = QLabel("UPDATE CHANNEL")
        ch_title.setStyleSheet("font-size: 10px; font-weight: 700; color: #8D929B;")
        self.channel_combo = QComboBox()
        self.channel_combo.addItem("Stable (Official Releases)", "stable")
        self.channel_combo.addItem("Beta (Prereleases & Previews)", "beta")
        idx = 1 if self.settings.update_channel.lower() == "beta" else 0
        self.channel_combo.setCurrentIndex(idx)
        self.channel_combo.currentIndexChanged.connect(self._on_channel_changed)
        ch_col.addWidget(ch_title)
        ch_col.addWidget(self.channel_combo)
        info_row.addLayout(ch_col)

        info_row.addStretch()

        # Check for updates button
        self.check_btn = QPushButton("Check for Updates")
        self.check_btn.setObjectName("primaryBtn")
        self.check_btn.setMinimumHeight(36)
        self.check_btn.setFixedWidth(160)
        self.check_btn.clicked.connect(self._on_check_clicked)
        info_row.addWidget(self.check_btn, alignment=Qt.AlignmentFlag.AlignVCenter)

        u_layout.addLayout(info_row)

        # Status & Last Update Check Row
        status_row = QHBoxLayout()
        self.status_lbl = QLabel("Ready to check GitHub Releases")
        self.status_lbl.setStyleSheet("color: #9BA3AF; font-size: 12px; font-weight: 500;")
        self.last_check_lbl = QLabel(f"Last checked: {self.settings.last_update_check or 'Never'}")
        self.last_check_lbl.setStyleSheet("color: #6C7280; font-size: 11px;")
        status_row.addWidget(self.status_lbl)
        status_row.addStretch()
        status_row.addWidget(self.last_check_lbl)
        u_layout.addLayout(status_row)

        # Release Notes Browser
        rn_label = QLabel("RELEASE NOTES:")
        rn_label.setStyleSheet("font-size: 10px; font-weight: 700; color: #21D789; letter-spacing: 0.5px;")
        u_layout.addWidget(rn_label)

        self.notes_browser = QTextBrowser()
        self.notes_browser.setMaximumHeight(85)
        self.notes_browser.setStyleSheet("""
            QTextBrowser {
                background: #141618;
                border: 1px solid #2B303A;
                border-radius: 4px;
                color: #C5CBD5;
                font-size: 12px;
                padding: 6px;
            }
        """)
        self.notes_browser.setPlaceholderText("Release notes will appear here when an update is discovered...")
        u_layout.addWidget(self.notes_browser)

        # Download Progress
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0, 100)
        u_layout.addWidget(self.progress_bar)

        # Action Buttons Row (Download / Install update button)
        action_row = QHBoxLayout()
        self.auto_check_cb = QCheckBox("Automatically check for updates on application startup")
        self.auto_check_cb.setChecked(self.settings.auto_check_updates)
        self.auto_check_cb.toggled.connect(self._save_auto_check)
        action_row.addWidget(self.auto_check_cb)
        action_row.addStretch()

        self.download_btn = QPushButton("Download Update")
        self.download_btn.setVisible(False)
        self.download_btn.clicked.connect(self._on_download_clicked)
        action_row.addWidget(self.download_btn)

        self.install_btn = QPushButton("Install Update & Restart")
        self.install_btn.setObjectName("primaryBtn")
        self.install_btn.setVisible(False)
        self.install_btn.clicked.connect(self._on_install_clicked)
        action_row.addWidget(self.install_btn)

        u_layout.addLayout(action_row)

        root.addWidget(update_card)

        # -------------------------------------------------------------
        # 2. HARDWARE CONNECTION CARD
        # -------------------------------------------------------------
        hw_card = self._create_card("HARDWARE INTERFACE CONFIGURATION")
        hw_layout = hw_card.layout()

        p_row = QHBoxLayout()
        p_label = QLabel("Serial Port (Arduino Uno):")
        p_label.setFixedWidth(190)
        self.port_combo = QComboBox()
        self.port_combo.setMinimumWidth(180)
        self.refresh_ports_btn = QPushButton("Scan Ports")
        self.refresh_ports_btn.setFixedWidth(100)
        self.refresh_ports_btn.clicked.connect(self.refresh_ports)
        p_row.addWidget(p_label)
        p_row.addWidget(self.port_combo)
        p_row.addWidget(self.refresh_ports_btn)
        p_row.addStretch()
        hw_layout.addLayout(p_row)

        b_row = QHBoxLayout()
        b_label = QLabel("Baud Rate:")
        b_label.setFixedWidth(190)
        self.baud_combo = QComboBox()
        self.baud_combo.setMinimumWidth(180)
        for rate in ["9600", "19200", "38400", "57600", "115200", "230400", "460800"]:
            self.baud_combo.addItem(rate)
        self.baud_combo.setCurrentText(str(self.settings.baud_rate))
        b_row.addWidget(b_label)
        b_row.addWidget(self.baud_combo)
        b_row.addStretch()
        hw_layout.addLayout(b_row)

        apply_hw_btn = QPushButton("Apply Hardware Settings")
        apply_hw_btn.setFixedWidth(180)
        apply_hw_btn.clicked.connect(self._apply_hardware)
        hw_layout.addWidget(apply_hw_btn)

        root.addWidget(hw_card)

        # -------------------------------------------------------------
        # 3. USER DATA PRESERVATION CARD
        # -------------------------------------------------------------
        data_card = self._create_card("USER DATA & CALIBRATION PRESERVATION")
        d_layout = data_card.layout()

        appdata_path = str(get_app_data_dir())
        d_info = QLabel(
            "User configuration, calibration profiles, and historical measurements "
            "are preserved in standard OS AppData and are never overwritten during software updates."
        )
        d_info.setWordWrap(True)
        d_info.setStyleSheet("color: #9BA3AF; font-size: 11px;")
        d_layout.addWidget(d_info)

        path_label = QLabel(f"Path: {appdata_path}")
        path_label.setStyleSheet("color: #61AFEF; font-family: monospace; font-size: 11px;")
        d_layout.addWidget(path_label)

        open_folder_btn = QPushButton("Open AppData Folder")
        open_folder_btn.setFixedWidth(160)
        open_folder_btn.clicked.connect(self._open_data_folder)
        d_layout.addWidget(open_folder_btn)

        root.addWidget(data_card)
        root.addStretch()

        self.refresh_ports()

    def _create_card(self, title_text: str) -> QFrame:
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background: #181A1D;
                border: 1px solid #2B303A;
                border-radius: 8px;
            }
            QLabel { border: none; }
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(10)

        header = QLabel(title_text)
        header.setStyleSheet("font-size: 11px; font-weight: 700; color: #21D789; letter-spacing: 0.5px; border: none;")
        layout.addWidget(header)
        return card

    def refresh_ports(self):
        self.port_combo.clear()
        ports = serial.tools.list_ports.comports()
        preferred_index = 0
        for idx, p in enumerate(ports):
            desc = f"{p.device} — {p.description}"
            self.port_combo.addItem(desc, p.device)
            if p.device == self.settings.serial_port:
                preferred_index = idx

        if not ports:
            self.port_combo.addItem(self.settings.serial_port, self.settings.serial_port)
        else:
            self.port_combo.setCurrentIndex(preferred_index)

    def _apply_hardware(self):
        port = self.port_combo.currentData() or self.settings.serial_port
        baud = int(self.baud_combo.currentText())
        self.settings.serial_port = port
        self.settings.baud_rate = baud
        self.settings.save()
        self.connection_changed.emit(port, baud)
        QMessageBox.information(self, "Hardware Updated", f"Serial interface configured:\nPort: {port}\nBaud: {baud}")

    def _on_channel_changed(self):
        new_channel = self.channel_combo.currentData()
        self.settings.update_channel = new_channel
        self.settings.save()
        self.status_lbl.setText(f"Channel set to {new_channel.upper()}. Click 'Check for Updates' to scan.")

    def _save_auto_check(self):
        self.settings.auto_check_updates = self.auto_check_cb.isChecked()
        self.settings.save()

    def _on_check_clicked(self):
        channel = self.channel_combo.currentData()
        self.status_lbl.setText(f"Checking GitHub Releases ({channel.upper()} channel)...")
        self.status_lbl.setStyleSheet("color: #E5C07B;")
        self.check_btn.setEnabled(False)
        self.download_btn.setVisible(False)
        self.install_btn.setVisible(False)
        self.check_updates_requested.emit(channel)

    def _on_download_clicked(self):
        if self.staged_release_data:
            self.status_lbl.setText("Downloading installer asset from GitHub...")
            self.status_lbl.setStyleSheet("color: #61AFEF;")
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            self.download_btn.setEnabled(False)
            self.download_update_requested.emit(self.staged_release_data)

    def _on_install_clicked(self):
        self.install_update_requested.emit()

    def handle_update_available(self, release_data: dict):
        self.staged_release_data = release_data
        tag = release_data.get("tag_name", "")
        self.latest_ver_lbl.setText(tag)
        self.latest_ver_lbl.setStyleSheet("font-size: 16px; font-weight: 700; color: #21D789; font-family: monospace;")
        self.status_lbl.setText(f"Update available: {tag}")
        self.status_lbl.setStyleSheet("color: #21D789; font-weight: 600;")
        self.check_btn.setEnabled(True)

        # Display Release Notes
        notes = release_data.get("body", "No release notes available.")
        self.notes_browser.setMarkdown(notes)

        # Show Download button
        self.download_btn.setVisible(True)
        self.download_btn.setEnabled(True)
        self.download_btn.setText(f"Download {tag}")

        self.last_check_lbl.setText(f"Last checked: {self.settings.last_update_check or 'Just now'}")

    def handle_up_to_date(self, message: str):
        self.status_lbl.setText(message)
        self.status_lbl.setStyleSheet("color: #9BA3AF;")
        self.check_btn.setEnabled(True)
        self.download_btn.setVisible(False)
        self.install_btn.setVisible(False)
        self.last_check_lbl.setText(f"Last checked: {self.settings.last_update_check or 'Just now'}")

    def handle_update_error(self, err_msg: str):
        self.status_lbl.setText(f"Check failed: {err_msg}")
        self.status_lbl.setStyleSheet("color: #E06C75;")
        self.check_btn.setEnabled(True)

    def handle_download_progress(self, downloaded: int, total: int, percent: float):
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(int(percent))
        mb_down = downloaded / (1024 * 1024)
        mb_total = total / (1024 * 1024)
        self.status_lbl.setText(f"Downloading: {mb_down:.1f} MB / {mb_total:.1f} MB ({percent:.0f}%)")

    def handle_ready_to_install(self):
        self.progress_bar.setVisible(False)
        self.status_lbl.setText("Download & verification complete! (SHA-256 and digital signature verified)")
        self.status_lbl.setStyleSheet("color: #21D789; font-weight: 600;")
        self.download_btn.setVisible(False)
        self.install_btn.setVisible(True)
        self.install_btn.setEnabled(True)

    def _open_data_folder(self):
        folder = str(get_app_data_dir())
        if sys.platform == "win32":
            os.startfile(folder)
        else:
            import subprocess
            subprocess.Popen(["xdg-open" if sys.platform != "darwin" else "open", folder])
