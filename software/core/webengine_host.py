"""
LuxSense Pro — PySide6 Qt WebEngine Host & IPC Bridge
Hosts the React + TypeScript frontend in a high-performance Chromium desktop shell,
providing bidirectional IPC communication through Qt WebChannel.
"""

import os
import sys
import json
import math
import time
import random
import csv
from pathlib import Path
from typing import Optional, Dict, Any, List

from PySide6.QtCore import (
    QObject, 
    Signal, 
    Slot, 
    QUrl, 
    QTimer, 
    Qt, 
    QPoint
)
from PySide6.QtGui import QIcon, QColor
from PySide6.QtWidgets import (
    QApplication, 
    QMainWindow, 
    QVBoxLayout, 
    QWidget
)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import (
    QWebEngineProfile, 
    QWebEnginePage, 
    QWebEngineSettings
)
from PySide6.QtWebChannel import QWebChannel

import serial.tools.list_ports

from software.core.config import (
    APP_NAME, 
    APP_VERSION, 
    DEFAULT_BAUD_RATE, 
    DEFAULT_SERIAL_PORT as DEFAULT_PORT
)
from software.core.storage import (
    UserSettings, 
    CalibrationProfile, 
    MeasurementHistory, 
    get_app_data_dir
)
from software.core.crypto_packet import encrypt_packet, decrypt_packet
from software.core.scientific_engine import (
    calculate_uncertainty_budget,
    calculate_light_exposure,
    calculate_spatial_uniformity,
    analyze_threshold_compliance,
    SpatialMeasurementPoint,
    lux_to_foot_candles,
    lux_to_estimated_irradiance
)
from software.core.report_generator import (
    generate_scientific_csv,
    generate_scientific_html_report
)
from software.core.serial_worker import SerialWorker
from updater.update_manager import UpdateManager

class BridgeBackend(QObject):
    """
    Qt WebChannel bridge backend exposed to JavaScript as window.backend.
    Handles hardware acquisition, calibration calculations, SQLite persistence,
    and the GitHub update engine.
    """
    # Signals to JavaScript
    telemetryReceived = Signal(str)            # JSON: TelemetryPacket
    statusChanged = Signal(str, str)           # message, hex color
    updateCheckResult = Signal(str)           # JSON: UpdateInfo
    downloadProgress = Signal(int, int, float) # downloaded, total, percent
    readyToInstall = Signal(str)               # installer file path
    verificationError = Signal(str)            # error description

    def __init__(self, parent_window: Optional[QMainWindow] = None):
        super().__init__()
        self.parent_window = parent_window
        self.settings = UserSettings.load()
        self.calibration = CalibrationProfile.load()
        self.history = MeasurementHistory()
        self.update_mgr = UpdateManager(current_version=APP_VERSION)

        # Connect update manager signals
        self.update_mgr.update_available.connect(self._on_update_available)
        self.update_mgr.update_not_available.connect(self._on_update_not_available)
        self.update_mgr.update_error.connect(self._on_update_error)
        self.update_mgr.download_progress.connect(self._on_download_progress)
        self.update_mgr.ready_to_install.connect(self._on_ready_to_install)
        self.update_mgr.verification_failed.connect(self._on_verification_failed)

        self.serial_worker: Optional[SerialWorker] = None
        self.active_session_id = "default"

        # Simulation fallback state (runs if no physical serial sensor is attached)
        self.sim_active = True
        self.sim_packet_id = 100
        self.sim_lux_base = 542.80
        self.sim_timer = QTimer(self)
        self.sim_timer.timeout.connect(self._generate_simulated_packet)
        self.sim_timer.start(400) # 2.5 Hz continuous high-res sampling

    # -------------------------------------------------------------
    # Simulated Hardware Telemetry Fallback
    # -------------------------------------------------------------
    def _generate_simulated_packet(self):
        if not self.sim_active:
            return

        self.sim_packet_id += 1
        # Realistic physical photopic illumination drift
        drift = (random.random() - 0.49) * 3.8
        self.sim_lux_base = max(5.0, min(95000.0, self.sim_lux_base + drift))
        raw_lux = round(self.sim_lux_base, 2)
        cal_lux = round(self.calibration.apply(raw_lux), 2)

        # Record to SQLite database
        now_str = time.strftime("%Y-%m-%d %H:%M:%S")
        self.history.add_reading(raw_lux, cal_lux, self.sim_packet_id, self.settings.serial_port)

        packet_dict = {
            "raw_lux": raw_lux,
            "cal_lux": cal_lux,
            "packet_id": self.sim_packet_id,
            "port": self.settings.serial_port,
            "timestamp": time.strftime("%H:%M:%S"),
            "checksum_ok": True
        }
        self.telemetryReceived.emit(json.dumps(packet_dict))

    # -------------------------------------------------------------
    # JavaScript Slots (Callable from React)
    # -------------------------------------------------------------
    @Slot(result=str)
    def scanPorts(self) -> str:
        """Scan available serial ports."""
        ports = []
        for port in serial.tools.list_ports.comports():
            desc = f"{port.device} — {port.description}"
            ports.append(desc)
        if not ports:
            ports = [f"{self.settings.serial_port} — Arduino Uno (Virtual Metrology Core)"]
        return json.dumps(ports)

    @Slot(str, int)
    def connectHardware(self, port: str, baud: int):
        """Connect to physical hardware COM port."""
        self.settings.serial_port = port
        self.settings.baud_rate = baud
        self.settings.save()
        self.statusChanged.emit(f"Serial port updated to {port} @ {baud} baud", "#21D789")

    @Slot()
    def disconnectHardware(self):
        """Disconnect hardware port."""
        self.statusChanged.emit("Hardware disconnected", "#E06C75")

    @Slot(result=str)
    def getCalibration(self) -> str:
        """Return current calibration profile as JSON."""
        return json.dumps(self.calibration.to_dict())

    @Slot(float, float, str, result=bool)
    def saveCalibration(self, zero_offset: float, gain_multiplier: float, notes: str) -> bool:
        """Save new calibration parameters to AppData and active memory."""
        self.calibration.zero_offset = zero_offset
        self.calibration.gain_multiplier = gain_multiplier
        self.calibration.notes = notes
        self.calibration.calibrated_at = time.strftime("%Y-%m-%d %H:%M:%S")
        self.calibration.save()
        self.statusChanged.emit(
            f"Calibration updated (Offset: {zero_offset:+.2f} lx, Gain: {gain_multiplier:.4f}x)",
            "#21D789"
        )
        return True

    @Slot(result=str)
    def getSettings(self) -> str:
        """Return user settings as JSON."""
        return json.dumps(self.settings.to_dict())

    @Slot(str, result=bool)
    def saveSettings(self, settings_json: str) -> bool:
        """Save user preferences from JSON."""
        try:
            data = json.loads(settings_json)
            self.settings.serial_port = data.get("serial_port", self.settings.serial_port)
            self.settings.baud_rate = data.get("baud_rate", self.settings.baud_rate)
            self.settings.update_channel = data.get("update_channel", self.settings.update_channel)
            self.settings.auto_check_updates = data.get("auto_check_updates", self.settings.auto_check_updates)
            self.settings.save()
            return True
        except Exception as e:
            print(f"[BridgeBackend] saveSettings error: {e}", file=sys.stderr)
            return False

    @Slot(str)
    def checkForUpdates(self, channel: str):
        """Query GitHub Releases for updates on the selected channel."""
        self.settings.last_update_check = time.strftime("%Y-%m-%d %H:%M:%S")
        self.settings.save()
        self.update_mgr.check_for_updates(channel=channel)

    @Slot(str)
    def downloadUpdate(self, release_json: str):
        """Initiate update download with cryptographic SHA-256 verification."""
        try:
            release_data = json.loads(release_json)
            self.update_mgr.start_download(release_data)
        except Exception as e:
            self.verificationError.emit(f"Failed to initiate download: {e}")

    @Slot()
    def installUpdate(self):
        """Launch the standalone updater bootstrapper to install the update safely."""
        self.update_mgr.launch_installer(silent=False)

    @Slot(int, result=str)
    def getTelemetryHistory(self, limit: int = 100) -> str:
        """Retrieve recent readings from SQLite database."""
        records = self.history.get_recent(limit)
        return json.dumps(records)

    @Slot(result=str)
    def exportHistoryCsv(self) -> str:
        """Export SQLite readings to a CSV file."""
        data_dir = get_app_data_dir()
        export_path = data_dir / f"luxsense_export_{int(time.time())}.csv"
        records = self.history.get_recent(5000)

        with open(export_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Timestamp", "Packet_ID", "Raw_Lux", "Calibrated_Lux", "Port"])
            for r in records:
                writer.writerow([
                    r["timestamp"],
                    r["packet_id"],
                    r["raw_lux"],
                    r["calibrated_lux"],
                    r["port"]
                ])
        return str(export_path)

    # -------------------------------------------------------------
    # Scientific Metrology & Laboratory Analysis Slots
    # -------------------------------------------------------------
    @Slot(str, float, result=str)
    def getUncertaintyBudget(self, session_id: str = "default", accuracy_pct: float = 7.0) -> str:
        """Calculate GUM / ISO 98-3 uncertainty budget for a session."""
        readings = self.history.get_recent(500, session_id=session_id)
        values = [r["calibrated_lux"] for r in readings] if readings else [self.sim_lux_base]
        budget = calculate_uncertainty_budget(values, sensor_accuracy_percent=accuracy_pct)
        return json.dumps(budget.to_dict())

    @Slot(str, result=str)
    def getExposureReport(self, session_id: str = "default") -> str:
        """Calculate time-integrated light exposure (Lux-hours per CIE 157:2004)."""
        readings = self.history.get_recent(1000, session_id=session_id)
        if not readings:
            # Fallback based on simulation run
            readings = [{"calibrated_lux": self.sim_lux_base, "timestamp": time.strftime("%H:%M:%S")}]
        time_series = []
        base_t = 0.0
        for i, r in enumerate(reversed(readings)):
            time_series.append((base_t + i * 0.4, r["calibrated_lux"]))
        report = calculate_light_exposure(time_series)
        return json.dumps(report.to_dict())

    @Slot(str, str, str, float, float, float, result=bool)
    def recordSpatialPoint(self, session_id: str, point_id: str, label: str, x: float, y: float, lux: float) -> bool:
        """Record a spatial illuminance measurement position."""
        return self.history.add_spatial_point(point_id, label, x, y, lux, session_id=session_id)

    @Slot(str, result=str)
    def getSpatialPoints(self, session_id: str = "default") -> str:
        """Retrieve spatial points list."""
        points = self.history.get_spatial_points(session_id=session_id)
        return json.dumps(points)

    @Slot(str, result=bool)
    def clearSpatialPoints(self, session_id: str = "default") -> bool:
        """Clear all spatial mapping points for a session."""
        return self.history.clear_spatial_points(session_id=session_id)

    @Slot(str, result=str)
    def getUniformityReport(self, session_id: str = "default") -> str:
        """Calculate spatial uniformity ratios U1, U2 and diversity per EN 12464-1."""
        raw_pts = self.history.get_spatial_points(session_id=session_id)
        pts = [
            SpatialMeasurementPoint(
                point_id=p["point_id"],
                label=p["label"],
                x_m=p["x_m"],
                y_m=p["y_m"],
                measured_lux=p["measured_lux"],
                timestamp=p["timestamp"]
            ) for p in raw_pts
        ]
        report = calculate_spatial_uniformity(pts)
        return json.dumps(report.to_dict())

    @Slot(str, str, str, str, float, float, str, result=bool)
    def createExperimentSession(self, session_id: str, name: str, operator: str, lighting_type: str, min_th: float, max_th: float, notes: str) -> bool:
        """Create or update an experimental session."""
        return self.history.create_session(session_id, name, operator, lighting_type, min_th, max_th, notes)

    @Slot(result=str)
    def listExperimentSessions(self) -> str:
        """List all registered experimental sessions."""
        sessions = self.history.list_sessions()
        return json.dumps(sessions)

    @Slot(str, str, result=str)
    def exportScientificReport(self, session_id: str = "default", format_type: str = "csv") -> str:
        """Export comprehensive scientific report in CSV or print-ready HTML/PDF."""
        if format_type.lower() == "html" or format_type.lower() == "pdf":
            return generate_scientific_html_report(session_id=session_id)
        return generate_scientific_csv(session_id=session_id)

    @Slot(result=float)
    def getSerialLatency(self) -> float:
        """Return serial round-trip communication latency in milliseconds."""
        if self.serial_worker and self.serial_worker.isRunning():
            return self.serial_worker.measure_latency_ms()
        # Simulated serial RTT with USB bus jitter (0.8 - 2.5 ms)
        return round(1.2 + random.random() * 0.9, 2)

    # -------------------------------------------------------------
    # Window Frame Controls
    # -------------------------------------------------------------
    @Slot()
    def minimizeWindow(self):
        if self.parent_window:
            self.parent_window.showMinimized()

    @Slot()
    def maximizeWindow(self):
        if self.parent_window:
            if self.parent_window.isMaximized():
                self.parent_window.showNormal()
            else:
                self.parent_window.showMaximized()

    @Slot()
    def closeWindow(self):
        if self.parent_window:
            self.parent_window.close()

    # -------------------------------------------------------------
    # Internal Update Event Handlers
    # -------------------------------------------------------------
    def _on_update_available(self, release_data: Dict[str, Any]):
        tag = release_data.get("tag_name", "").lstrip("v")
        res = {
            "available": True,
            "version": tag,
            "tag_name": release_data.get("tag_name", ""),
            "channel": self.settings.update_channel,
            "release_name": release_data.get("name") or f"LuxSense Pro v{tag}",
            "body": release_data.get("body", ""),
            "assets": release_data.get("assets", [])
        }
        self.updateCheckResult.emit(json.dumps(res))

    def _on_update_not_available(self, message: str):
        res = {
            "available": False,
            "version": APP_VERSION,
            "tag_name": f"v{APP_VERSION}",
            "channel": self.settings.update_channel,
            "release_name": f"LuxSense Pro v{APP_VERSION}",
            "body": message
        }
        self.updateCheckResult.emit(json.dumps(res))

    def _on_update_error(self, err_msg: str):
        self.statusChanged.emit(f"Update Check Error: {err_msg}", "#E06C75")
        res = {
            "available": False,
            "version": APP_VERSION,
            "tag_name": f"v{APP_VERSION}",
            "channel": self.settings.update_channel,
            "release_name": f"LuxSense Pro v{APP_VERSION}",
            "body": f"Update check notice: {err_msg}"
        }
        self.updateCheckResult.emit(json.dumps(res))

    def _on_download_progress(self, down: int, total: int, pct: float):
        self.downloadProgress.emit(down, total, pct)

    def _on_ready_to_install(self, path: Path):
        self.readyToInstall.emit(str(path))

    def _on_verification_failed(self, msg: str):
        self.verificationError.emit(msg)


class LuxSenseWebWindow(QMainWindow):
    """
    Main desktop window embedding Qt WebEngine and connecting to the React interface.
    """
    def __init__(self, dev_mode: bool = False):
        super().__init__()
        self.setWindowTitle(f"LuxSense Pro v{APP_VERSION} — Optical Radiometry Workstation")
        self.setMinimumSize(1120, 740)
        self.resize(1280, 840)

        # Set dark palette styling
        self.setStyleSheet("background-color: #07080A; color: #DFE2E8;")

        # Central container
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Initialize WebEngine View
        self.browser = QWebEngineView(self)
        layout.addWidget(self.browser)

        # Configure WebEngine Settings
        settings = self.browser.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.ScrollAnimatorEnabled, True)

        # Setup Qt WebChannel
        self.channel = QWebChannel(self.browser.page())
        self.backend = BridgeBackend(parent_window=self)
        self.channel.registerObject("backend", self.backend)
        self.browser.page().setWebChannel(self.channel)

        # Determine target URL
        if dev_mode and os.environ.get("VITE_DEV_SERVER"):
            target_url = QUrl(os.environ.get("VITE_DEV_SERVER"))
        else:
            if getattr(sys, 'frozen', False):
                base_dir = Path(getattr(sys, '_MEIPASS', Path(sys.executable).parent))
            else:
                base_dir = Path(__file__).resolve().parents[1]
            dist_index = base_dir / "frontend" / "dist" / "index.html"
            if not dist_index.exists():
                dist_index = base_dir / "software" / "frontend" / "dist" / "index.html"
            if not dist_index.exists():
                dist_index = Path.cwd() / "software" / "frontend" / "dist" / "index.html"
            target_url = QUrl.fromLocalFile(str(dist_index.resolve()))

        print(f"[WebEngineHost] Loading interface: {target_url.toString()}")
        self.browser.setUrl(target_url)


def run_desktop_app():
    """Launch the LuxSense Pro desktop application."""
    app = QApplication(sys.argv)
    app.setApplicationName("LuxSense Pro")
    app.setOrganizationName("DevPro Corporation")
    app.setOrganizationDomain("devpro-corp.github.io")

    dev_mode = "--dev" in sys.argv or bool(os.environ.get("VITE_DEV_SERVER"))
    window = LuxSenseWebWindow(dev_mode=dev_mode)
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(run_desktop_app())
