"""
LuxSense Pro — Calibration Tab UI
Provides precision photometric calibration profiles (Zero-offset and Gain Multiplier).
All changes are saved persistently to %APPDATA%/DevPro/LuxSensePro/calibration.json.
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QDoubleSpinBox, QPushButton, QFrame, QMessageBox, QTextEdit
)
from software.core.storage import CalibrationProfile

class CalibrationTab(QWidget):
    calibration_updated = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.profile = CalibrationProfile.load()
        self._init_ui()

    def _init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(18)

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
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)

        header = QLabel("OPTICAL METROLOGY & SENSOR CALIBRATION")
        header.setStyleSheet("font-size: 11px; font-weight: 700; color: #21D789; letter-spacing: 0.5px;")
        layout.addWidget(header)

        desc = QLabel(
            "Calibrate your BH1750 photodiode response. Calibration curve applies:\n"
            "Calibrated Lux = (Raw Lux + Zero Offset) × Gain Multiplier"
        )
        desc.setStyleSheet("color: #9BA3AF; font-size: 12px;")
        layout.addWidget(desc)

        # Zero offset
        z_row = QHBoxLayout()
        z_label = QLabel("Dark Offset (Zero Calibration) [lx]:")
        z_label.setFixedWidth(240)
        self.zero_spin = QDoubleSpinBox()
        self.zero_spin.setRange(-50.0, 50.0)
        self.zero_spin.setSingleStep(0.1)
        self.zero_spin.setDecimals(2)
        self.zero_spin.setValue(self.profile.zero_offset)
        z_row.addWidget(z_label)
        z_row.addWidget(self.zero_spin)
        z_row.addStretch()
        layout.addLayout(z_row)

        # Gain Multiplier
        g_row = QHBoxLayout()
        g_label = QLabel("Optical Gain Multiplier (Span Calibration):")
        g_label.setFixedWidth(240)
        self.gain_spin = QDoubleSpinBox()
        self.gain_spin.setRange(0.1, 10.0)
        self.gain_spin.setSingleStep(0.01)
        self.gain_spin.setDecimals(4)
        self.gain_spin.setValue(self.profile.gain_multiplier)
        g_row.addWidget(g_label)
        g_row.addWidget(self.gain_spin)
        g_row.addStretch()
        layout.addLayout(g_row)

        # Notes
        n_label = QLabel("Calibration Certificate / Lab Notes:")
        layout.addWidget(n_label)
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(70)
        self.notes_edit.setStyleSheet("background: #141618; border: 1px solid #2B303A; border-radius: 4px; color: #DFE1E5;")
        self.notes_edit.setText(self.profile.notes)
        layout.addWidget(self.notes_edit)

        # Buttons
        btn_row = QHBoxLayout()
        reset_btn = QPushButton("Reset to Factory Defaults")
        reset_btn.clicked.connect(self._reset_defaults)

        save_btn = QPushButton("Save Calibration Profile")
        save_btn.setObjectName("primaryBtn")
        save_btn.clicked.connect(self._save_profile)

        btn_row.addWidget(reset_btn)
        btn_row.addStretch()
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

        root.addWidget(card)
        root.addStretch()

    def _save_profile(self):
        self.profile.zero_offset = self.zero_spin.value()
        self.profile.gain_multiplier = self.gain_spin.value()
        self.profile.notes = self.notes_edit.toPlainText().strip()
        self.profile.save()
        self.calibration_updated.emit()
        QMessageBox.information(self, "Calibration Saved", "Photometric calibration parameters saved to persistent storage.")

    def _reset_defaults(self):
        self.zero_spin.setValue(0.0)
        self.gain_spin.setValue(1.0)
        self.notes_edit.setText("Standard BH1750 high-resolution mode (1 lx resolution)")
        self._save_profile()

