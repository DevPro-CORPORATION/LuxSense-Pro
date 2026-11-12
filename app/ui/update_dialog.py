"""
LuxSense Pro — Update Dialog UI
Modern, scientific instrumentation styled dialog displaying available updates,
changelogs, download progress, and confirmation actions.
"""

from pathlib import Path
from typing import Dict, Any, Optional
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTextBrowser, QProgressBar, QFrame
)
from app.core.config import APP_VERSION

class UpdateDialog(QDialog):
    install_confirmed = pyqtSignal(dict)
    postponed = pyqtSignal(str)

    def __init__(self, release_data: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.release_data = release_data
        self.new_version = release_data.get("tag_name", "").lstrip("v")
        self.setWindowTitle(f"Software Update Available — {release_data.get('name', 'LuxSense Pro')}")
        self.resize(580, 480)
        self.setStyleSheet("""
            QDialog { background: #181A1D; color: #E2E4E9; }
            QLabel { color: #E2E4E9; font-family: 'Segoe UI', sans-serif; }
            QFrame#card {
                background: #212429;
                border: 1px solid #333842;
                border-radius: 10px;
                padding: 16px;
            }
            QTextBrowser {
                background: #141618;
                border: 1px solid #2B303A;
                border-radius: 6px;
                color: #C5CBD5;
                font-family: 'Segoe UI', sans-serif;
                font-size: 13px;
                padding: 10px;
            }
            QPushButton {
                background: #2B303A;
                color: #FFFFFF;
                border: 1px solid #3E4554;
                border-radius: 6px;
                padding: 8px 18px;
                font-weight: 600;
                font-size: 13px;
            }
            QPushButton:hover { background: #383E4C; }
            QPushButton#primaryBtn {
                background: #21D789;
                color: #0E1A14;
                border: 1px solid #1EB976;
            }
            QPushButton#primaryBtn:hover { background: #28E895; }
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

        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(22, 20, 22, 20)

        # Header Card
        card = QFrame()
        card.setObjectName("card")
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(6)

        title = QLabel(f"LuxSense Pro v{self.new_version} is available")
        title.setStyleSheet("font-size: 18px; font-weight: 700; color: #FFFFFF;")
        
        info = QLabel(f"Currently installed: v{APP_VERSION}  •  Release date: {release_data.get('published_at', '')[:10]}")
        info.setStyleSheet("color: #9BA3AF; font-size: 12px;")

        card_layout.addWidget(title)
        card_layout.addWidget(info)
        layout.addWidget(card)

        # Changelog
        notes_label = QLabel("RELEASE NOTES & HIGHLIGHTS:")
        notes_label.setStyleSheet("font-weight: 700; font-size: 11px; color: #21D789; letter-spacing: 0.5px;")
        layout.addWidget(notes_label)

        self.notes_browser = QTextBrowser()
        body = release_data.get("body", "No release notes provided for this version.")
        # Render markdown/plain text nicely
        self.notes_browser.setMarkdown(body)
        layout.addWidget(self.notes_browser, 1)

        # Progress bar (hidden initially)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0, 100)
        layout.addWidget(self.progress_bar)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #E5C07B; font-size: 12px;")
        self.status_label.setVisible(False)
        layout.addWidget(self.status_label)

        # Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        self.postpone_btn = QPushButton("Remind Me Later")
        self.postpone_btn.clicked.connect(self._on_postpone)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)

        self.install_btn = QPushButton("Download & Update Now")
        self.install_btn.setObjectName("primaryBtn")
        self.install_btn.clicked.connect(self._on_install)

        btn_layout.addWidget(self.postpone_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.install_btn)
        layout.addLayout(btn_layout)

    def set_download_progress(self, downloaded: int, total: int, percent: float):
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(int(percent))
        self.status_label.setVisible(True)
        mb_down = downloaded / (1024 * 1024)
        mb_total = total / (1024 * 1024)
        self.status_label.setText(f"Downloading update payload... {mb_down:.1f} MB / {mb_total:.1f} MB ({percent:.0f}%)")
        self.install_btn.setEnabled(False)
        self.postpone_btn.setEnabled(False)

    def set_verifying(self):
        self.status_label.setText("Verifying SHA-256 checksum and Authenticode signature...")
        self.status_label.setStyleSheet("color: #61AFEF; font-size: 12px;")

    def _on_install(self):
        self.install_confirmed.emit(self.release_data)

    def _on_postpone(self):
        self.postponed.emit(self.release_data.get("tag_name", ""))
        self.accept()
