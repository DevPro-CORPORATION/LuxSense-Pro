"""
LuxSense Pro — Serial Worker Thread
Handles serial communication with Arduino Uno, device handshake, reading data,
and passing readings to UI and persistent history.
"""

import time
import serial
import serial.tools.list_ports
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
    data_signal = pyqtSignal(float, float, int, str)  # raw_lux, cal_lux, packet_id, port

    def __init__(self, port: str = "COM5", baud: int = DEFAULT_BAUD_RATE):
        super().__init__()
        self.port = port
        self.baud = baud
        self._running = True
        self.ser = None
        self.calibration = CalibrationProfile.load()
        self.history = MeasurementHistory()

    def update_config(self, port: str, baud: int):
        if self.port != port or self.baud != baud:
            self.port = port
            self.baud = baud
            self.close_serial()

    def reload_calibration(self):
        self.calibration = CalibrationProfile.load()

    def connect_sensor(self):
        self.status_signal.emit(f"Opening Arduino on {self.port}...", "#E5C07B")
        connection = serial.Serial(
            port=self.port,
            baudrate=self.baud,
            timeout=1.0,
            write_timeout=2.0
        )
        time.sleep(2.0)
        connection.reset_input_buffer()
        connection.write(DISCOVER_COMMAND)
        connection.flush()

        deadline = time.monotonic() + 5.0
        while self._running and time.monotonic() < deadline:
            response = connection.readline().decode("utf-8", errors="ignore").strip()
            if response == HANDSHAKE_TEXT:
                self.ser = connection
                return True

        connection.close()
        raise RuntimeError(f"No valid Arduino handshake on {self.port}. Expected {HANDSHAKE_TEXT}")

    def run(self):
        while self._running:
            try:
                if self.ser is None or not self.ser.is_open:
                    self.connect_sensor()
                    self.status_signal.emit(
                        f"Connected to Arduino on {self.port} — Handshake Verified",
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

            except (serial.SerialException, OSError, RuntimeError) as error:
                self.close_serial()
                if self._running:
                    self.status_signal.emit(f"Connection error: {error} — retrying...", "#E06C75")
                    self.msleep(1800)

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
        self.wait(3000)
        self.close_serial()
