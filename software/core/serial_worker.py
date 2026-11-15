"""
LuxSense Pro — Serial Worker Thread
Handles low-latency serial communication with Arduino Uno, hardware handshake,
encrypted packet decryption, dynamic state management, and passing real-time readings to UI and storage.
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
    status_signal = pyqtSignal(str, str)               # status text, hex color
    state_signal = pyqtSignal(str)                     # CONNECTING, SENSOR DETECTED, LIVE MEASUREMENT, DISCONNECTED, SENSOR ERROR
    data_signal = pyqtSignal(float, float, int, str)   # raw_lux, cal_lux, packet_id, port
    latency_signal = pyqtSignal(float)                 # round-trip latency in ms
    device_status_signal = pyqtSignal(bool, bool, str, str) # arduino_online, sensor_active, port, sensor_addr

    def __init__(self, port: str = "COM5", baud: int = DEFAULT_BAUD_RATE):
        super().__init__()
        self.port = port
        self.baud = baud
        self._running = True
        self.ser = None
        self.arduino_online = False
        self.sensor_active = False
        self.sensor_addr = ""
        self.calibration = CalibrationProfile.load()
        self.history = MeasurementHistory()
        self.last_latency_check = 0.0
        self.last_sensor_probe = 0.0
        self.current_state = "DISCONNECTED"

    def update_config(self, port: str, baud: int):
        if self.port != port or self.baud != baud:
            self.port = port
            self.baud = baud
            self.close_serial()

    def reload_calibration(self):
        self.calibration = CalibrationProfile.load()

    def _set_state(self, state: str, msg: str, color: str):
        self.current_state = state
        self.state_signal.emit(state)
        self.status_signal.emit(msg, color)

    def connect_sensor(self):
        self._set_state(
            "CONNECTING",
            f"CONNECTING — Probing Arduino Uno on {self.port} @ {self.baud} baud...",
            "#E5C07B"
        )
        self.device_status_signal.emit(False, False, self.port, "")
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
            if line.startswith(HANDSHAKE_TEXT):
                self.ser = connection
                self.arduino_online = True

                if "NO_SENSOR" in line:
                    self.sensor_active = False
                    self.sensor_addr = ""
                    self._set_state(
                        "SENSOR ERROR",
                        f"ARDUINO ONLINE ({self.port}) — BH1750 not detected at I2C 0x23 or 0x5C (Check wiring)",
                        "#E5C07B"
                    )
                    self.device_status_signal.emit(True, False, self.port, "")
                    return True

                addr_info = "0x23"
                if "ADDR_" in line:
                    addr_info = line.split("ADDR_")[-1]

                self.sensor_active = True
                self.sensor_addr = addr_info
                self._set_state(
                    "SENSOR DETECTED",
                    f"SENSOR DETECTED — BH1750 Active at {addr_info} on {self.port}",
                    "#61AFEF"
                )
                self.device_status_signal.emit(True, True, self.port, addr_info)
                return True

        connection.close()
        self.arduino_online = False
        self.sensor_active = False
        self.device_status_signal.emit(False, False, self.port, "")
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

                now = time.monotonic()
                # If Arduino is online but sensor is not responding, probe periodically without dropping connection
                if self.ser and self.ser.is_open and not self.sensor_active:
                    if now - self.last_sensor_probe >= 2.5:
                        self.last_sensor_probe = now
                        try:
                            self.ser.write(DISCOVER_COMMAND)
                            self.ser.flush()
                        except Exception:
                            pass

                line = self.ser.readline().decode("ascii", errors="ignore").strip()
                if not line:
                    continue

                # Handle hot-plug discovery response while port is connected
                if line.startswith(HANDSHAKE_TEXT):
                    if "NO_SENSOR" in line:
                        self.sensor_active = False
                        self.sensor_addr = ""
                        if self.current_state != "SENSOR ERROR":
                            self._set_state(
                                "SENSOR ERROR",
                                f"ARDUINO ONLINE ({self.port}) — BH1750 not detected at I2C 0x23 or 0x5C (Check wiring)",
                                "#E5C07B"
                            )
                        self.device_status_signal.emit(True, False, self.port, "")
                    else:
                        addr_info = "0x23"
                        if "ADDR_" in line:
                            addr_info = line.split("ADDR_")[-1]
                        self.sensor_active = True
                        self.sensor_addr = addr_info
                        self._set_state(
                            "SENSOR DETECTED",
                            f"SENSOR DETECTED — BH1750 Active at {addr_info} on {self.port}",
                            "#61AFEF"
                        )
                        self.device_status_signal.emit(True, True, self.port, addr_info)
                    continue

                # Handle explicit sensor error from firmware
                if line.startswith("ERR:"):
                    err_type = line.split("ERR:")[-1].strip()
                    self.sensor_active = False
                    if self.current_state != "SENSOR ERROR":
                        self._set_state(
                            "SENSOR ERROR",
                            f"ARDUINO ONLINE ({self.port}) — {err_type} (Check BH1750 I2C wiring)",
                            "#E5C07B"
                        )
                    self.device_status_signal.emit(True, False, self.port, "")
                    continue

                result = decrypt_packet(line)
                if result is not None:
                    packet_id, raw_lux = result
                    cal_lux = self.calibration.apply(raw_lux)
                    self.history.add_reading(raw_lux, cal_lux, packet_id, self.port)

                    if not self.sensor_active or not self.arduino_online:
                        self.sensor_active = True
                        self.arduino_online = True
                        self.device_status_signal.emit(True, True, self.port, self.sensor_addr or "0x23")

                    if self.current_state != "LIVE MEASUREMENT":
                        self._set_state(
                            "LIVE MEASUREMENT",
                            f"LIVE MEASUREMENT — {raw_lux:.2f} lx (Sample #{packet_id})",
                            "#21D789"
                        )

                    self.data_signal.emit(raw_lux, cal_lux, packet_id, self.port)

                # Periodic latency check every 4 seconds
                if now - self.last_latency_check >= 4.0:
                    self.last_latency_check = now
                    rtt = self.measure_latency_ms()
                    if rtt > 0:
                        self.latency_signal.emit(rtt)

            except (serial.SerialException, OSError, RuntimeError) as error:
                self.close_serial()
                self.arduino_online = False
                self.sensor_active = False
                self.device_status_signal.emit(False, False, self.port, "")
                if self._running:
                    self._set_state(
                        "DISCONNECTED",
                        f"DISCONNECTED — Port {self.port} unavailable. Waiting for device reconnection...",
                        "#E06C75"
                    )
                    self.msleep(2000)

        self.close_serial()

    def close_serial(self):
        self.arduino_online = False
        self.sensor_active = False
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
        self.close_serial()
        self.wait(2000)
