"""
LuxSense Pro — Serial Worker Thread
Handles low-latency serial communication with Arduino Uno, hardware handshake,
encrypted packet decryption, and passing real-time readings to UI and storage.
"""

import time
import serial
import serial.tools.list_ports
try:
    from PySide6.QtCore import QThread, Signal as pyqtSignal
except ImportError:
    from PyQt6.QtCore import QThread, pyqtSignal

from software.core.config import (
    DEFAULT_BAUD_RATE,
    HANDSHAKE_TEXT,
    DISCOVER_COMMAND,
    DISCONNECT_COMMAND
)
from software.core.crypto_packet import decrypt_packet
from software.core.storage import CalibrationProfile, MeasurementHistory

class SerialWorker(QThread):
    status_signal = pyqtSignal(str, str)
    data_signal = pyqtSignal(float, float, int, str)   # raw_lux, cal_lux, packet_id, port
    latency_signal = pyqtSignal(float)                 # round-trip latency in ms

    def __init__(self, port: str = "COM5", baud: int = DEFAULT_BAUD_RATE):
        super().__init__()
        self.port = port
        self.baud = baud
        self._running = True
        self.ser = None
        self.calibration = CalibrationProfile.load()
        self.history = MeasurementHistory()
        self.last_latency_check = 0.0

    def update_config(self, port: str, baud: int):
        if self.port != port or self.baud != baud:
            self.port = port
            self.baud = baud
            self.close_serial()

    def reload_calibration(self):
        self.calibration = CalibrationProfile.load()

    def connect_sensor(self):
        self.status_signal.emit(f"Connecting to Arduino Uno on {self.port} @ {self.baud} baud...", "#E5C07B")
        connection = serial.Serial(
            port=self.port,
            baudrate=self.baud,
            timeout=0.15,        # Low timeout for ultra-responsive read loop
            write_timeout=1.0
        )
        # Allow ATmega328P auto-reset to settle
        time.sleep(1.8)
        connection.reset_input_buffer()
        connection.write(DISCOVER_COMMAND)
        connection.flush()

        deadline = time.monotonic() + 4.0
        while self._running and time.monotonic() < deadline:
            line = connection.readline().decode("utf-8", errors="ignore").strip()
            if line == HANDSHAKE_TEXT:
                self.ser = connection
                return True

        connection.close()
        raise RuntimeError(f"No valid Arduino handshake on {self.port}. Expected {HANDSHAKE_TEXT}")

    def measure_latency_ms(self) -> float:
        """Measure serial round-trip latency (RTT) using PING command."""
        if not self.ser or not self.ser.is_open:
            return 0.0
        try:
            t0 = time.perf_counter()
            self.ser.write(b"PING\n")
            self.ser.flush()
            resp = self.ser.readline().decode("ascii", errors="ignore").strip()
            t1 = time.perf_counter()
            if resp == "PONG":
                rtt_ms = (t1 - t0) * 1000.0
                return round(rtt_ms, 2)
        except Exception:
            pass
        return 0.0

    def run(self):
        while self._running:
            try:
                if self.ser is None or not self.ser.is_open:
                    self.connect_sensor()
                    self.status_signal.emit(
                        f"Connected to Arduino on {self.port} — Handshake Verified (BH1750 Active)",
                        "#21D789"
                    )

                line = self.ser.readline().decode("ascii", errors="ignore").strip()
                if not line:
                    continue

                result = decrypt_packet(line)
                if result is not None:
                    packet_id, raw_lux = result
                    cal_lux = self.calibration.apply(raw_lux)
                    self.history.add_reading(raw_lux, cal_lux, packet_id, self.port)
                    self.data_signal.emit(raw_lux, cal_lux, packet_id, self.port)

                # Periodic latency check every 5 seconds
                now = time.monotonic()
                if now - self.last_latency_check >= 5.0:
                    self.last_latency_check = now
                    rtt = self.measure_latency_ms()
                    if rtt > 0:
                        self.latency_signal.emit(rtt)

            except (serial.SerialException, OSError, RuntimeError) as error:
                self.close_serial()
                if self._running:
                    self.status_signal.emit(f"Serial interface notice: {error} — reconnecting...", "#E06C75")
                    self.msleep(1500)

        self.close_serial()

    def close_serial(self):
        if self.ser is not None:
            try:
                if self.ser.is_open:
                    try:
                        self.ser.write(DISCONNECT_COMMAND)
                        self.ser.flush()
                    except Exception:
                        pass
                    self.ser.close()
            except (serial.SerialException, OSError):
                pass
            self.ser = None

    def stop(self):
        self._running = False
        self.wait(2000)
        self.close_serial()
