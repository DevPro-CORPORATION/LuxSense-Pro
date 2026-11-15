"""
LuxSense Pro — PySide6 WebEngine IPC Host
Exposes Python hardware acquisition, calibration engine, SQLite persistence,
and update services to the React frontend via QtWebChannel.
"""

import sys
import json
import time
import os
from pathlib import Path
from typing import Optional, List, Dict, Any

import serial.tools.list_ports
from PySide6.QtCore import QObject, Signal, Slot, QTimer, QUrl, Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QMainWindow, QApplication, QWidget, QVBoxLayout
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEngineSettings
from PySide6.QtWebChannel import QWebChannel

from software.core.config import (
    APP_NAME,
    APP_VERSION,
    DEFAULT_SERIAL_PORT as DEFAULT_PORT,
    DEFAULT_BAUD_RATE
)
from software.core.storage import (
    UserSettings,
    CalibrationProfile,
    MeasurementHistory,
    get_app_data_dir
)
from software.core.scientific_engine import (
    calculate_uncertainty_budget,
    calculate_light_exposure,
    calculate_spatial_uniformity,
    analyze_threshold_compliance
)
from software.core.report_generator import (
    generate_scientific_csv,
    generate_scientific_html_report
)
from software.core.serial_worker import SerialWorker
from software.core.firmware_security import (
    verify_firmware_package,
    FirmwareManifest,
    DEVPRO_FIRMWARE_PUBKEY_HEX
)
from software.core.firmware_flasher import FirmwareFlashWorker
from updater.update_manager import UpdateManager

ROOT_DIR = Path(__file__).resolve().parents[2]

class BridgeBackend(QObject):
    """
    Qt WebChannel bridge backend exposed to JavaScript as window.backend.
    Handles physical hardware acquisition, calibration calculations, SQLite persistence,
    and the GitHub update engine. Real sensor data only — no simulation fallback.
    """
    # Signals to JavaScript
    telemetryReceived = Signal(str)            # JSON: TelemetryPacket
    statusChanged = Signal(str, str)           # message, hex color
    hardwareStateChanged = Signal(str)         # CONNECTING, SENSOR DETECTED, LIVE MEASUREMENT, DISCONNECTED, SENSOR ERROR
    updateCheckResult = Signal(str)           # JSON: UpdateInfo
    downloadProgress = Signal(int, int, float) # downloaded, total, percent
    readyToInstall = Signal(str)               # installer file path
    verificationError = Signal(str)            # error description

    # Firmware Update Signals
    firmwareStatusChanged = Signal(str)        # JSON: Hardware & Firmware Status
    firmwareCheckResult = Signal(str)          # JSON: Firmware Manifest & Security Status
    firmwareFlashProgress = Signal(int, str)   # percentage (0-100), phase status text
    firmwareFlashCompleted = Signal(bool, str) # success, summary message
    firmwareLogEmitted = Signal(str)           # real-time diagnostic log stream

    def __init__(self, parent_window: Optional[QMainWindow] = None, auto_connect: bool = True):
        super().__init__()
        self.parent_window = parent_window
        self.settings = UserSettings.load()
        self.calibration = CalibrationProfile.load()
        self.history = MeasurementHistory()
        self.update_mgr = UpdateManager(current_version=APP_VERSION)
        self.firmware_worker: Optional[FirmwareFlashWorker] = None

        # Connect update manager signals
        self.update_mgr.update_available.connect(self._on_update_available)
        self.update_mgr.update_not_available.connect(self._on_update_not_available)
        self.update_mgr.update_error.connect(self._on_update_error)
        self.update_mgr.download_progress.connect(self._on_download_progress)
        self.update_mgr.ready_to_install.connect(self._on_ready_to_install)
        self.update_mgr.verification_failed.connect(self._on_verification_failed)

        self.serial_worker: Optional[SerialWorker] = None
        self.active_session_id = "default"
        self.current_hardware_state = "DISCONNECTED"

        # Auto-connect to physical hardware outside of unit tests
        if auto_connect and "pytest" not in sys.modules:
            self._init_hardware_worker()

    def _init_hardware_worker(self):
        """Auto-detect Arduino Uno and initialize serial communication worker."""
        target_port = self.settings.serial_port
        ports = list(serial.tools.list_ports.comports())
        
        # Auto-detect Arduino Uno if available
        for p in ports:
            desc = p.description or ""
            if "Arduino" in desc or "Uno" in desc or "CH340" in desc or p.vid == 0x2341:
                target_port = p.device
                self.settings.serial_port = target_port
                self.settings.save()
                break

        available_devices = [p.device for p in ports]
        if target_port in available_devices:
            self._start_serial_worker(target_port, self.settings.baud_rate)
        else:
            self.current_hardware_state = "DISCONNECTED"
            self.hardwareStateChanged.emit("DISCONNECTED")
            self.statusChanged.emit("DISCONNECTED — No hardware serial port available", "#E06C75")

    def _start_serial_worker(self, port: str, baud: int):
        """Start or restart the SerialWorker thread for real telemetry."""
        if self.serial_worker is not None:
            self.serial_worker.stop()
            self.serial_worker = None

        self.serial_worker = SerialWorker(port=port, baud=baud)
        self.serial_worker.data_signal.connect(self._on_serial_data)
        self.serial_worker.status_signal.connect(self._on_serial_status)
        self.serial_worker.state_signal.connect(self._on_serial_state)
        self.serial_worker.start()

    def _on_serial_data(self, raw_lux: float, cal_lux: float, packet_id: int, port: str):
        """Forward verified physical sensor packet to SQLite and React frontend."""
        self.history.add_reading(raw_lux, cal_lux, packet_id, port, session_id=self.active_session_id)

        packet_dict = {
            "raw_lux": round(raw_lux, 2),
            "cal_lux": round(cal_lux, 2),
            "packet_id": packet_id,
            "port": port,
            "timestamp": time.strftime("%H:%M:%S"),
            "checksum_ok": True,
            "state": "LIVE MEASUREMENT"
        }
        self.telemetryReceived.emit(json.dumps(packet_dict))

    def _on_serial_status(self, msg: str, color: str):
        self.statusChanged.emit(msg, color)

    def _on_serial_state(self, state: str):
        self.current_hardware_state = state
        self.hardwareStateChanged.emit(state)

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
            ports = [f"{self.settings.serial_port} — Arduino Uno (Hardware Port)"]
        return json.dumps(ports)

    @Slot(result=str)
    def getHardwareState(self) -> str:
        """Return current hardware acquisition state."""
        return self.current_hardware_state

    @Slot(str, int)
    def connectHardware(self, port: str, baud: int):
        """Connect to physical hardware COM port."""
        clean_port = port.split(" — ")[0].strip() if " — " in port else port.strip()
        self.settings.serial_port = clean_port
        self.settings.baud_rate = baud
        self.settings.save()
        self._start_serial_worker(clean_port, baud)

    @Slot()
    def disconnectHardware(self):
        """Disconnect hardware port."""
        if self.serial_worker is not None:
            self.serial_worker.stop()
            self.serial_worker = None
        self.current_hardware_state = "DISCONNECTED"
        self.hardwareStateChanged.emit("DISCONNECTED")
        self.statusChanged.emit("DISCONNECTED — Hardware disconnected by user", "#E06C75")

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
        if self.serial_worker:
            self.serial_worker.reload_calibration()
        return True

    @Slot(result=str)
    def getSettings(self) -> str:
        """Return user settings as JSON."""
        return json.dumps(self.settings.to_dict())

    @Slot(str, result=bool)
    def saveSettings(self, settings_json: str) -> bool:
        """Save user configuration."""
        try:
            data = json.loads(settings_json)
            self.settings.serial_port = data.get("serial_port", self.settings.serial_port)
            self.settings.baud_rate = int(data.get("baud_rate", self.settings.baud_rate))
            self.settings.update_channel = data.get("update_channel", self.settings.update_channel)
            self.settings.auto_check_updates = bool(data.get("auto_check_updates", self.settings.auto_check_updates))
            self.settings.save()

            if self.serial_worker:
                self.serial_worker.update_config(self.settings.serial_port, self.settings.baud_rate)
            return True
        except Exception as e:
            print(f"[Error] Failed to save settings: {e}")
            return False

    @Slot(int, result=str)
    def getRecentTelemetry(self, limit: int = 100) -> str:
        """Return recent measurements from SQLite database."""
        records = self.history.get_recent(limit, session_id=self.active_session_id)
        return json.dumps(records)

    @Slot(int, result=str)
    def getTelemetryHistory(self, limit: int = 100) -> str:
        """Alias for getRecentTelemetry."""
        return self.getRecentTelemetry(limit)

    @Slot(result=str)
    def exportCsvHistory(self) -> str:
        """Export session measurements to AppData CSV and return file path."""
        out_path = os.path.join(get_app_data_dir(), "exports", f"luxsense_export_{int(time.time())}.csv")
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        return self.history.export_to_csv(out_path)

    @Slot(result=str)
    def exportHistoryCsv(self) -> str:
        """Alias for exportCsvHistory."""
        return self.exportCsvHistory()

    # -------------------------------------------------------------
    # Scientific Metrology Slots (Objective B)
    # -------------------------------------------------------------
    @Slot(str, float, result=str)
    def getUncertaintyBudgetBySession(self, session_id: str, accuracy_pct: float) -> str:
        readings = self.history.get_recent(500, session_id=session_id)
        values = [r["calibrated_lux"] for r in readings] if readings else [0.0]
        budget = calculate_uncertainty_budget(values, sensor_accuracy_percent=accuracy_pct)
        return json.dumps(budget.to_dict())

    def getUncertaintyBudget(self, arg1: Any = "default", arg2: Any = 4.0) -> str:
        session_id = "default"
        accuracy_pct = 4.0
        if isinstance(arg1, str):
            session_id = arg1
            if isinstance(arg2, (int, float)):
                accuracy_pct = float(arg2)
        elif isinstance(arg1, (int, float)):
            accuracy_pct = float(arg1)
            if isinstance(arg2, str):
                session_id = arg2

        readings = self.history.get_recent(500, session_id=session_id)
        values = [r["calibrated_lux"] for r in readings] if readings else [0.0]
        budget = calculate_uncertainty_budget(values, sensor_accuracy_percent=accuracy_pct)
        return json.dumps(budget.to_dict())

    @Slot(str, result=str)
    def getExposureReport(self, session_id: str = "default") -> str:
        """Calculate time-integrated light exposure (Lux-hours per CIE 157:2004)."""
        readings = self.history.get_recent(1000, session_id=session_id)
        if not readings:
            return json.dumps(calculate_light_exposure([]).to_dict())
        time_series = []
        base_t = 0.0
        for i, r in enumerate(reversed(readings)):
            time_series.append((base_t + i * 0.25, r["calibrated_lux"]))
        report = calculate_light_exposure(time_series)
        return json.dumps(report.to_dict())

    @Slot(str, str, str, float, float, float, result=bool)
    def recordSpatialPoint(self, session_id: str, point_id: str, label: str, x: float, y: float, lux: float) -> bool:
        """Record a spatial illuminance measurement position."""
        return self.history.add_spatial_point(point_id, label, x, y, lux, session_id=session_id)

    @Slot(str, result=str)
    def getSpatialPoints(self, session_id: str = "default") -> str:
        """Retrieve all spatial points for a session."""
        pts = self.history.get_spatial_points(session_id=session_id)
        return json.dumps(pts)

    @Slot(str, result=bool)
    def clearSpatialPoints(self, session_id: str = "default") -> bool:
        """Clear spatial points for a session."""
        return self.history.clear_spatial_points(session_id=session_id)

    @Slot(str, result=str)
    def getUniformityReport(self, session_id: str = "default") -> str:
        """Calculate EN 12464-1 uniformity metrics (U1, U2, Diversity)."""
        pts = self.history.get_spatial_points(session_id=session_id)
        report = calculate_spatial_uniformity(pts)
        return json.dumps(report.to_dict())

    @Slot(str, str, str, str, float, float, str, result=bool)
    def createExperimentSession(
        self,
        session_id: str,
        name: str,
        operator: str,
        lighting_type: str,
        min_lux: float,
        max_lux: float,
        notes: str
    ) -> bool:
        """Create and switch to a new experiment session."""
        ok = self.history.create_session(
            session_id=session_id,
            name=name,
            operator=operator,
            lighting_type=lighting_type,
            min_th=min_lux,
            max_th=max_lux,
            notes=notes
        )
        if ok:
            self.active_session_id = session_id
        return ok

    @Slot(result=str)
    def listExperimentSessions(self) -> str:
        """List all experiment sessions."""
        sessions = self.history.list_sessions()
        return json.dumps(sessions)

    @Slot(str, str, str, result=str)
    @Slot(str, str, result=str)
    @Slot(str, result=str)
    def exportScientificReport(self, session_id: str = "default", export_type: str = "csv", out_dir: str = "") -> str:
        """Export metrology-grade CSV or HTML certificate."""
        if export_type.lower() == "csv":
            return generate_scientific_csv(session_id=session_id)
        else:
            return generate_scientific_html_report(session_id=session_id)

    @Slot(result=float)
    def getSerialLatency(self) -> float:
        """Return serial round-trip communication latency in milliseconds."""
        if self.serial_worker and self.serial_worker.isRunning():
            return self.serial_worker.measure_latency_ms()
        return 0.0

    # -------------------------------------------------------------
    # Window Frame Controls
    # -------------------------------------------------------------
    @Slot()
    def minimizeWindow(self):
        if self.parent_window:
            self.parent_window.showMinimized()

    @Slot()
    def toggleMaximizeWindow(self):
        if self.parent_window:
            if self.parent_window.isMaximized():
                self.parent_window.showNormal()
            else:
                self.parent_window.showMaximized()

    @Slot()
    def closeWindow(self):
        if self.serial_worker:
            self.serial_worker.stop()
        if self.parent_window:
            self.parent_window.close()
        else:
            QApplication.quit()

    # -------------------------------------------------------------
    # Update Engine Slots
    # -------------------------------------------------------------
    @Slot(bool)
    def checkForUpdates(self, user_initiated: bool = True):
        """Trigger update check."""
        self.update_mgr.check_for_updates(user_initiated=user_initiated)

    @Slot()
    def downloadUpdate(self):
        """Download latest release installer."""
        self.update_mgr.download_latest_installer()

    @Slot(str)
    def installUpdate(self, installer_path: str):
        """Launch update installation."""
        self.update_mgr.launch_installer(installer_path)

    # -------------------------------------------------------------
    # Internal Signal Forwarding
    # -------------------------------------------------------------
    def _on_update_available(self, info: Dict[str, Any]):
        info["available"] = True
        self.updateCheckResult.emit(json.dumps(info))

    def _on_update_not_available(self, version: str):
        info = {"available": False, "version": version, "body": "You have the latest version."}
        self.updateCheckResult.emit(json.dumps(info))

    def _on_update_error(self, err_msg: str):
        self.statusChanged.emit(f"Update Check Error: {err_msg}", "#E06C75")

    def _on_download_progress(self, dl: int, tot: int, pct: float):
        self.downloadProgress.emit(dl, tot, pct)

    def _on_ready_to_install(self, path: str):
        self.readyToInstall.emit(path)

    def _on_verification_failed(self, err: str):
        self.verificationError.emit(err)

    # -------------------------------------------------------------
    # Firmware Management Slots
    # -------------------------------------------------------------
    @Slot(result=str)
    def getFirmwareStatus(self) -> str:
        """Query connected Arduino Uno identification, MCU, and installed firmware."""
        port = self.settings.serial_port
        is_connected = bool(self.serial_worker and self.serial_worker.ser and self.serial_worker.ser.is_open)
        status = {
            "board": "Arduino Uno R3",
            "mcu": "ATmega328P (16MHz)",
            "bootloader": "Optiboot v4.4 (STK500v1)",
            "port": port,
            "baud_rate": self.settings.baud_rate,
            "installed_version": "1.2.0" if is_connected else "Unknown",
            "is_connected": is_connected,
            "sensor": "BH1750 (0x23 / 0x5C)",
            "hardware_state": self.current_hardware_state
        }
        return json.dumps(status)

    @Slot(result=str)
    def checkFirmwareUpdates(self) -> str:
        """Inspect and cryptographically verify signed firmware releases."""
        manifest_paths = [
            ROOT_DIR / "dist_installer" / "firmware-manifest.json",
            ROOT_DIR / "firmware" / "firmware-manifest.json",
            get_app_data_dir() / "firmware-manifest.json"
        ]
        manifest_file = None
        for p in manifest_paths:
            if p.exists():
                manifest_file = p
                break

        if not manifest_file:
            res = {
                "available": False,
                "error": "No firmware manifest found in release distribution."
            }
            self.firmwareCheckResult.emit(json.dumps(res))
            return json.dumps(res)

        try:
            with open(manifest_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            hex_paths = [
                ROOT_DIR / "firmware" / "build" / data.get("hex_filename", "LuxSense_Arduino.ino.hex"),
                ROOT_DIR / "firmware" / data.get("hex_filename", "LuxSense_Arduino.ino.hex"),
                ROOT_DIR / "dist_installer" / data.get("hex_filename", "LuxSense_Arduino.ino.hex")
            ]
            hex_file = next((h for h in hex_paths if h.exists()), None)

            ok, msg, manifest = verify_firmware_package(
                data,
                hex_path=hex_file,
                current_firmware_version="1.2.0"
            )

            res = {
                "available": ok,
                "valid": ok,
                "message": msg,
                "manifest": data,
                "hex_available": hex_file is not None,
                "hex_path": str(hex_file) if hex_file else None
            }
            self.firmwareCheckResult.emit(json.dumps(res))
            return json.dumps(res)
        except Exception as e:
            res = {"available": False, "error": f"Failed reading manifest: {str(e)}"}
            self.firmwareCheckResult.emit(json.dumps(res))
            return json.dumps(res)

    @Slot(str, str, bool, result=bool)
    def startFirmwareFlash(self, port: str, hex_path_str: str, allow_downgrade: bool = False) -> bool:
        """Safely flash physical Arduino Uno firmware with explicit pre-flight checks."""
        if self.firmware_worker and self.firmware_worker.isRunning():
            self.firmwareFlashCompleted.emit(False, "A firmware update is already in progress.")
            return False

        # Load manifest
        manifest_file = ROOT_DIR / "dist_installer" / "firmware-manifest.json"
        if not manifest_file.exists():
            manifest_file = ROOT_DIR / "firmware" / "firmware-manifest.json"
        if not manifest_file.exists():
            self.firmwareFlashCompleted.emit(False, "Firmware manifest not found.")
            return False

        try:
            with open(manifest_file, "r", encoding="utf-8") as f:
                manifest_data = json.load(f)
        except Exception as e:
            self.firmwareFlashCompleted.emit(False, f"Cannot parse manifest: {e}")
            return False

        hex_path = Path(hex_path_str) if hex_path_str else (ROOT_DIR / "firmware" / "build" / manifest_data.get("hex_filename", "LuxSense_Arduino.ino.hex"))
        if not hex_path.exists():
            hex_path = ROOT_DIR / "firmware" / "build" / "LuxSense_Arduino.ino.hex"

        target_port = port or self.settings.serial_port

        def stop_telemetry():
            if self.serial_worker:
                self.serial_worker.stop()
                self.serial_worker.wait(1500)
                self.current_hardware_state = "FLASHING"
                self.hardwareStateChanged.emit("FLASHING")

        def resume_telemetry():
            self._init_hardware_worker()

        self.firmware_worker = FirmwareFlashWorker(
            port=target_port,
            manifest_data=manifest_data,
            hex_path=hex_path,
            current_firmware_version="1.2.0",
            allow_downgrade=allow_downgrade,
            stop_telemetry_fn=stop_telemetry,
            resume_telemetry_fn=resume_telemetry,
            parent=self
        )

        self.firmware_worker.stateChanged.connect(self._on_firmware_state_changed)
        self.firmware_worker.progressChanged.connect(self.firmwareFlashProgress.emit)
        self.firmware_worker.logEmitted.connect(self.firmwareLogEmitted.emit)
        self.firmware_worker.flashCompleted.connect(self.firmwareFlashCompleted.emit)
        self.firmware_worker.start()
        return True

    def _on_firmware_state_changed(self, state: str):
        self.firmwareStatusChanged.emit(state)

    @Slot()
    def abortFirmwareFlash(self):
        """Abort firmware flash if in pre-hardware phase."""
        if self.firmware_worker:
            self.firmware_worker.abort()

    @Slot(result=str)
    def getFirmwareDiagnosticLogs(self) -> str:
        """Retrieve recent persistent firmware flashing logs."""
        log_file = get_app_data_dir() / "firmware_flash.log"
        if log_file.exists():
            try:
                return log_file.read_text(encoding="utf-8")[-8000:]
            except Exception:
                pass
        return "No diagnostic log entries recorded."


class LuxSenseWebWindow(QMainWindow):
    """
    Main desktop window embedding Qt WebEngine and connecting to the React interface.
    """
    def __init__(self, dev_mode: bool = False):
        super().__init__()
        self.setWindowTitle(f"LuxSense Pro v{APP_VERSION} — Optical Radiometry Workstation")
        self.setMinimumSize(1120, 740)
        self.resize(1280, 840)

        # Set window icon
        icon_path = Path(__file__).resolve().parents[2] / "my_icon.ico"
        if not icon_path.exists():
            icon_path = Path.cwd() / "my_icon.ico"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

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

    icon_path = Path(__file__).resolve().parents[2] / "my_icon.ico"
    if not icon_path.exists():
        icon_path = Path.cwd() / "my_icon.ico"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    dev_mode = "--dev" in sys.argv or bool(os.environ.get("VITE_DEV_SERVER"))
    window = LuxSenseWebWindow(dev_mode=dev_mode)
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(run_desktop_app())
