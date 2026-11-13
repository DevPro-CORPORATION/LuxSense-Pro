"""
LuxSense Pro — Analytics & Telemetry History Tab
Visualizes historical lux measurements from persistent SQLite storage,
computes statistical aggregates, and allows data export.
"""

import csv
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QPushButton,
    QFrame, QFileDialog, QMessageBox
)
from software.core.storage import MeasurementHistory

class AnalyticsTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.history = MeasurementHistory()
        self._init_ui()

    def _init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(14)

        # Stats Cards Row
        stats_row = QHBoxLayout()
        stats_row.setSpacing(12)

        self.samples_card = self._create_stat_card("TOTAL SAMPLES", "0")
        self.min_card = self._create_stat_card("MINIMUM LUX", "-- lx")
        self.avg_card = self._create_stat_card("AVERAGE LUX", "-- lx")
        self.max_card = self._create_stat_card("MAXIMUM LUX", "-- lx")

        stats_row.addWidget(self.samples_card)
        stats_row.addWidget(self.min_card)
        stats_row.addWidget(self.avg_card)
        stats_row.addWidget(self.max_card)
        root.addLayout(stats_row)

        # Table & Actions
        table_header = QHBoxLayout()
        t_label = QLabel("RECENT TELEMETRY LOGS (PERSISTENT SQLite DB):")
        t_label.setStyleSheet("font-size: 11px; font-weight: 700; color: #21D789; letter-spacing: 0.5px;")
        table_header.addWidget(t_label)
        table_header.addStretch()

        refresh_btn = QPushButton("Refresh Table")
        refresh_btn.setFixedWidth(110)
        refresh_btn.clicked.connect(self.refresh_data)

        export_btn = QPushButton("Export CSV")
        export_btn.setFixedWidth(100)
        export_btn.clicked.connect(self._export_csv)

        table_header.addWidget(refresh_btn)
        table_header.addWidget(export_btn)
        root.addLayout(table_header)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Timestamp", "Packet #", "Raw (lx)", "Calibrated (lx)", "Port"])
        self.table.setStyleSheet("""
            QTableWidget {
                background: #141618;
                border: 1px solid #2B303A;
                border-radius: 6px;
                gridline-color: #262A33;
                color: #DFE1E5;
            }
            QHeaderView::section {
                background: #1E2126;
                color: #9BA3AF;
                padding: 6px;
                border: 1px solid #2B303A;
                font-weight: 600;
            }
        """)
        self.table.horizontalHeader().setStretchLastSection(True)
        root.addWidget(self.table, 1)

        self.refresh_data()

    def _create_stat_card(self, title: str, initial_val: str) -> QFrame:
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background: #181A1D;
                border: 1px solid #2B303A;
                border-radius: 8px;
                padding: 8px;
            }
        """)
        l = QVBoxLayout(card)
        l.setSpacing(4)
        t = QLabel(title)
        t.setStyleSheet("color: #8D929B; font-size: 10px; font-weight: 700; border: none;")
        v = QLabel(initial_val)
        v.setStyleSheet("color: #21D789; font-size: 18px; font-weight: 700; border: none;")
        l.addWidget(t)
        l.addWidget(v)
        card.val_label = v
        return card

    def refresh_data(self):
        records = self.history.get_recent(limit=100)
        self.table.setRowCount(len(records))

        lux_values = []
        for row_idx, r in enumerate(records):
            self.table.setItem(row_idx, 0, QTableWidgetItem(str(r["timestamp"])))
            self.table.setItem(row_idx, 1, QTableWidgetItem(str(r["packet_id"])))
            self.table.setItem(row_idx, 2, QTableWidgetItem(f"{r['raw_lux']:.2f}"))
            self.table.setItem(row_idx, 3, QTableWidgetItem(f"{r['calibrated_lux']:.2f}"))
            self.table.setItem(row_idx, 4, QTableWidgetItem(str(r["port"])))
            lux_values.append(r["calibrated_lux"])

        total_count = self.history.get_count()
        self.samples_card.val_label.setText(str(total_count))

        if lux_values:
            min_l = min(lux_values)
            max_l = max(lux_values)
            avg_l = sum(lux_values) / len(lux_values)
            self.min_card.val_label.setText(f"{min_l:.1f} lx")
            self.max_card.val_label.setText(f"{max_l:.1f} lx")
            self.avg_card.val_label.setText(f"{avg_l:.1f} lx")
        else:
            self.min_card.val_label.setText("-- lx")
            self.max_card.val_label.setText("-- lx")
            self.avg_card.val_label.setText("-- lx")

    def _export_csv(self):
        records = self.history.get_recent(limit=5000)
        if not records:
            QMessageBox.information(self, "No Data", "No measurement records available to export.")
            return

        file_path, _ = QFileDialog.getSaveFileName(self, "Export Telemetry Log", "luxsense_telemetry.csv", "CSV Files (*.csv)")
        if not file_path:
            return

        try:
            with open(file_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=["timestamp", "packet_id", "raw_lux", "calibrated_lux", "port"])
                writer.writeheader()
                writer.writerows(records)
            QMessageBox.information(self, "Export Success", f"Successfully exported {len(records)} records to {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export CSV: {e}")
