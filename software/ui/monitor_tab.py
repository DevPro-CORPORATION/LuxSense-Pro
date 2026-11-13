"""
LuxSense Pro — Live Monitor Tab UI
Real-time illuminance gauge, rolling-key XOR verification status, and device indicators.
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame
)

class MonitorTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 22)
        layout.addStretch(1)

        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background: #181A1D;
                border: 1px solid #2B303A;
                border-radius: 14px;
            }
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(28, 28, 28, 28)
        card_layout.setSpacing(14)

        heading = QLabel("REAL-TIME CALIBRATED ILLUMINANCE")
        heading.setAlignment(Qt.AlignmentFlag.AlignCenter)
        heading.setStyleSheet("color: #A0A5AE; font-size: 12px; font-weight: 700; letter-spacing: 1px; border: none;")

        self.lux_value = QLabel("--.-- lx")
        self.lux_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lux_value.setMinimumHeight(100)
        self.lux_value.setStyleSheet("""
            color: #21D789;
            font-size: 54px;
            font-weight: 700;
            font-family: monospace;
            padding: 8px;
            border: none;
        """)

        self.raw_info = QLabel("Raw: --.-- lx | Calibration Gain: 1.0000 | Offset: 0.00 lx")
        self.raw_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.raw_info.setStyleSheet("color: #7E8590; font-size: 11px; border: none;")

        self.packet_info = QLabel("Waiting for verified sensor data...")
        self.packet_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.packet_info.setWordWrap(True)
        self.packet_info.setStyleSheet("color: #A7ABB3; font-size: 12px; border: none;")

        card_layout.addWidget(heading)
        card_layout.addWidget(self.lux_value)
        card_layout.addWidget(self.raw_info)
        card_layout.addWidget(self.packet_info)
        layout.addWidget(card)
        layout.addStretch(1)

    def update_reading(self, raw_lux: float, cal_lux: float, packet_id: int, port: str):
        self.lux_value.setText(f"{cal_lux:.2f} lx")
        self.raw_info.setText(f"Raw: {raw_lux:.2f} lx  •  Calibrated (Stored in history.db)")
        self.packet_info.setText(
            f"Verified Packet #{packet_id}  |  Port: {port}  |  "
            "Checksum: OK  |  Rolling-128 XOR"
        )
