"""
LuxSense Pro — Settings Tab UI
Provides hardware connection parameters, automated/manual update controls,
version comparisons, and persistent data storage transparency.
"""

import os
import sys
import serial.tools.list_ports
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QCheckBox, QPushButton, QFrame,
    QProgressBar, QMessageBox
)

from app.core.config import (
    APP_VERSION,
    DEFAULT_BAUD_RATE,
    get_app_data_dir,
    WEBSITE_URL,
    GITHUB_REPO_URL
)
from app.core.storage import UserSettings

class SettingsTab(QWidget):
    connection_changed = pyqtSignal(str, int)
    check_updates_requested = pyqtSignal()
    open_url_requested = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings = UserSettings.load()
        self._init_ui()

    def _init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(18)

        # 1. HARDWARE CONNECTION CARD
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

        root.addWidget(hw_card)

        # 2. SOFTWARE UPDATE MANAGER CARD
        update_card = self._create_card("SOFTWARE UPDATES & RELEASE CHANNELS")
        u_layout = update_card.layout()

        # Current vs published version
        v_row = QHBoxLayout()
        v_current_label = QLabel("Installed Version:")
        v_current_label.setFixedWidth(190)
        self.v_current_val = QLabel(f"v{APP_VERSION} (Official)")
        self.v_current_val.setStyleSheet("color: #21D789; font-weight: 700;")
        
        self.check_btn = QPushButton("Check for Updates")
        self.check_btn.setObjectName("primaryBtn")
        self.check_btn.setFixedWidth(160)
        self.check_btn.clicked.connect(self._on_check_clicked)

        v_row.addWidget(v_current_label)
        v_row.addWidget(self.v_current_val)
        v_row.addStretch()
        v_row.addWidget(self.check_btn)
        u_layout.addLayout(v_row)

        # Status & Last checked
        s_row = QHBoxLayout()
        s_title = QLabel("Update Status:")
        s_title.setFixedWidth(190)
        self.status_text = QLabel("Ready to check")
        self.status_text.setStyleSheet("color: #9BA3AF;")
        s_row.addWidget(s_title)
        s_row.addWidget(self.status_text)
        s_row.addStretch()
        u_layout.addLayout(s_row)

        self.last_check_label = QLabel(f"Last checked: {self.settings.last_update_check or 'Never'}")
        self.last_check_label.setStyleSheet("color: #6C7280; font-size: 11px;")
        u_layout.addWidget(self.last_check_label)

        # Checkboxes
        self.auto_check_cb = QCheckBox("Check for updates automatically on application startup")
        self.auto_check_cb.setChecked(self.settings.auto_check_updates)
        self.auto_check_cb.toggled.connect(self._save_settings)
        u_layout.addWidget(self.auto_check_cb)

        self.prerelease_cb = QCheckBox("Include preview and pre-release builds (DevPro Insider channel)")
        self.prerelease_cb.setChecked(self.settings.include_prereleases)
        self.prerelease_cb.toggled.connect(self._save_settings)
        u_layout.addWidget(self.prerelease_cb)

        # Progress bar
        self.update_progress = QProgressBar()
        self.update_progress.setVisible(False)
        u_layout.addWidget(self.update_progress)

        root.addWidget(update_card)

        # 3. DATA INTEGRITY & STORAGE CARD
        data_card = self._create_card("USER DATA & PROFILE PRESERVATION")
        d_layout = data_card.layout()

        appdata_path = str(get_app_data_dir())
        d_info = QLabel(
            "User configuration, calibration profiles, and historical sensor telemetry "
            "are stored in standard Windows AppData. They are preserved intact across updates."
        )
        d_info.setWordWrap(True)
        d_info.setStyleSheet("color: #9BA3AF; font-size: 12px;")
        d_layout.addWidget(d_info)

        path_label = QLabel(f"Storage path: {appdata_path}")
        path_label.setStyleSheet("color: #61AFEF; font-family: 'Consolas', monospace; font-size: 11px;")
        d_layout.addWidget(path_label)

        open_folder_btn = QPushButton("Open Data Folder")
        open_folder_btn.setFixedWidth(140)
        open_folder_btn.clicked.connect(self._open_data_folder)
        d_layout.addWidget(open_folder_btn)

        root.addWidget(data_card)
        root.addStretch()

        # Save connection button
        save_hw_btn = QPushButton("Apply Hardware Settings")
        save_hw_btn.setObjectName("primaryBtn")
        save_hw_btn.clicked.connect(self._apply_hardware)
        root.addWidget(save_hw_btn)

        self.refresh_ports()

    def _create_card(self, title_text: str) -> QFrame:
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background: #1E2126;
                border: 1px solid #2F343F;
                border-radius: 8px;
            }
            QLabel { border: none; }
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 16, 18, 16)
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
        QMessageBox.information(self, "Settings Saved", f"Serial settings updated:\nPort: {port}\nBaud: {baud}")

    def _save_settings(self):
        self.settings.auto_check_updates = self.auto_check_cb.isChecked()
        self.settings.include_prereleases = self.prerelease_cb.isChecked()
        self.settings.save()

    def _on_check_clicked(self):
        self.status_text.setText("Checking GitHub Releases...")
        self.status_text.setStyleSheet("color: #E5C07B;")
        self.check_btn.setEnabled(False)
        self.check_updates_requested.emit()

    def set_update_status(self, text: str, color: str = "#9BA3AF"):
        self.status_text.setText(text)
        self.status_text.setStyleSheet(f"color: {color};")
        self.check_btn.setEnabled(True)
        self.last_check_label.setText(f"Last checked: {self.settings.last_update_check or 'Just now'}")

    def _open_data_folder(self):
        folder = str(get_app_data_dir())
        if sys.platform == "win32":
            os.startfile(folder)
        else:
            import subprocess
            subprocess.Popen(["xdg-open" if sys.platform != "darwin" else "open", folder])
