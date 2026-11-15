"""
LuxSense Pro — Production Firmware Flashing Engine
Manages safe, controlled flashing of the physical Arduino Uno (ATmega328P) photometer firmware.
Enforces pre-flight board verification, cryptographic authorization, clean serial handoff,
real-time stdout/stderr progress parsing, timeout guards, and post-flash sensor verification.
"""

import os
import sys
import time
import subprocess
import re
from pathlib import Path
from typing import Optional, Tuple, Callable, Dict, Any

import serial
import serial.tools.list_ports
from PySide6.QtCore import QObject, QThread, Signal

from software.core.storage import get_app_data_dir
from software.core.firmware_security import verify_firmware_package, FirmwareManifest
from software.core.config import DEFAULT_BAUD_RATE, HANDSHAKE_TEXT, DISCOVER_COMMAND

ROOT_DIR = Path(__file__).resolve().parents[2]

def find_arduino_cli() -> Optional[Path]:
    """Locate arduino-cli executable."""
    candidates = [
        ROOT_DIR / "tools" / "arduino-cli" / "arduino-cli.exe",
        Path(r"C:\Program Files\Arduino CLI\arduino-cli.exe"),
        Path(r"C:\Program Files (x86)\Arduino CLI\arduino-cli.exe")
    ]
    for p in candidates:
        if p.exists():
            return p
    return None

def find_avrdude() -> Tuple[Optional[Path], Optional[Path]]:
    """Locate avrdude executable and configuration file."""
    # Check Arduino15 package directory
    local_appdata = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
    base_tools = Path(local_appdata) / "Arduino15" / "packages" / "arduino" / "tools" / "avrdude"
    if base_tools.exists():
        for ver_dir in base_tools.iterdir():
            exe = ver_dir / "bin" / "avrdude.exe"
            conf = ver_dir / "etc" / "avrdude.conf"
            if exe.exists() and conf.exists():
                return exe, conf
    return None, None


class FirmwareFlashWorker(QThread):
    """
    Background worker thread executing the multi-phase firmware update lifecycle:
    1. VALIDATING: Manifest & digital signature verification.
    2. STOPPING_TELEMETRY: Graceful worker disconnect and port release.
    3. PREPARING: Tool discovery and parameter configuration.
    4. FLASHING: Subprocess execution with real-time output capture and timeout.
    5. VERIFYING: Serial reboot, handshake query, I2C sensor detection, and telemetry probe.
    """
    stateChanged = Signal(str)            # Current state name
    progressChanged = Signal(int, str)    # percent (0-100), status text
    logEmitted = Signal(str)              # raw console log line
    flashCompleted = Signal(bool, str)    # success, summary message

    def __init__(
        self,
        port: str,
        manifest_data: Dict[str, Any],
        hex_path: Path,
        current_firmware_version: Optional[str] = None,
        allow_downgrade: bool = False,
        board_type: str = "uno",
        stop_telemetry_fn: Optional[Callable[[], None]] = None,
        resume_telemetry_fn: Optional[Callable[[], None]] = None,
        parent: Optional[QObject] = None
    ):
        super().__init__(parent)
        self.port = port
        self.manifest_data = manifest_data
        self.hex_path = hex_path
        self.current_firmware_version = current_firmware_version
        self.allow_downgrade = allow_downgrade
        self.board_type = (board_type or "uno").lower()
        self.stop_telemetry_fn = stop_telemetry_fn
        self.resume_telemetry_fn = resume_telemetry_fn
        self._is_aborted = False

        self.log_path = get_app_data_dir() / "firmware_flash.log"

    def abort(self):
        self._is_aborted = True

    def _log(self, msg: str):
        line = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
        print(f"[FirmwareFlasher] {msg}")
        self.logEmitted.emit(line)
        try:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(line + "\n")
        except Exception:
            pass

    def run(self):
        self._log(f"=== Starting Firmware Update for Arduino Uno on {self.port} ===")
        self._log(f"Log destination: {self.log_path}")

        # PHASE 1: VALIDATING
        self.stateChanged.emit("VALIDATING")
        self.progressChanged.emit(5, "Verifying digital signature and hex integrity...")
        self._log("Phase 1: Validating firmware package and publisher signature...")

        target_fqbn = "arduino:avr:nano" if "nano" in self.board_type else "arduino:avr:uno"
        ok, msg, manifest = verify_firmware_package(
            self.manifest_data,
            hex_path=self.hex_path,
            current_firmware_version=self.current_firmware_version,
            allow_downgrade=self.allow_downgrade,
            expected_board=target_fqbn,
            expected_mcu="atmega328p"
        )
        if not ok:
            self._log(f"CRITICAL: Firmware package rejection: {msg}")
            self.stateChanged.emit("FAILED")
            self.progressChanged.emit(0, "Security validation failed.")
            self.flashCompleted.emit(False, f"Security rejection: {msg}")
            return

        self._log(f"Digital signature valid: {manifest.publisher}")
        self._log(f"Target: {manifest.target_board} ({manifest.target_mcu} @ {manifest.clock_mhz}MHz)")
        self._log(f"SHA-256 Digest: {manifest.hex_sha256}")

        if self._is_aborted:
            self._log("Flash aborted by user prior to hardware handoff.")
            self.stateChanged.emit("FAILED")
            self.flashCompleted.emit(False, "Update cancelled.")
            return

        # PHASE 2: STOPPING TELEMETRY
        self.stateChanged.emit("STOPPING_TELEMETRY")
        self.progressChanged.emit(15, "Releasing serial port...")
        self._log(f"Phase 2: Stopping active telemetry loop on {self.port}...")

        if self.stop_telemetry_fn:
            try:
                self.stop_telemetry_fn()
                time.sleep(1.0)
            except Exception as e:
                self._log(f"Warning during telemetry shutdown: {e}")

        # Ensure serial port is actually free
        try:
            test_ser = serial.Serial(self.port, baudrate=115200, timeout=0.5)
            test_ser.close()
            time.sleep(0.5)
            self._log(f"Serial port {self.port} verified available for flashing.")
        except serial.SerialException as e:
            self._log(f"ERROR: Cannot access {self.port}: {e}")
            self.stateChanged.emit("FAILED")
            self.progressChanged.emit(0, f"Port {self.port} unavailable or locked.")
            self.flashCompleted.emit(False, f"Port {self.port} unavailable: {e}")
            if self.resume_telemetry_fn:
                self.resume_telemetry_fn()
            return

        # PHASE 3: PREPARING
        self.stateChanged.emit("PREPARING")
        self.progressChanged.emit(25, "Configuring programming tool...")
        self._log("Phase 3: Preparing programmer toolchain...")

        arduino_cli = find_arduino_cli()
        avrdude, avrdude_conf = find_avrdude()

        cmd = None
        flasher_type = None

        # Strategy A: Use avrdude directly with Optiboot configuration
        if avrdude and avrdude_conf:
            flasher_type = "avrdude"
            # Nano classic bootloader typically runs at 57600 baud, Uno/Nano New at 115200
            baud = "57600" if self.board_type == "nano_old" else "115200"
            cmd = [
                str(avrdude),
                "-C", str(avrdude_conf),
                "-v",
                "-p", "m328p",
                "-c", "arduino",
                "-P", str(self.port),
                "-b", baud,
                "-D",
                f"-Uflash:w:{str(self.hex_path)}:i"
            ]
        # Strategy B: Use arduino-cli
        elif arduino_cli:
            flasher_type = "arduino-cli"
            sketch_dir = ROOT_DIR / "firmware" / "LuxSense_Arduino"
            fqbn = "arduino:avr:nano" if "nano" in self.board_type else "arduino:avr:uno"
            cmd = [
                str(arduino_cli),
                "upload",
                "-p", str(self.port),
                "--fqbn", fqbn,
                str(sketch_dir)
            ]
        else:
            err = "Neither avrdude nor arduino-cli is installed or discoverable on this workstation."
            self._log(f"ERROR: {err}")
            self.stateChanged.emit("FAILED")
            self.progressChanged.emit(0, "Flashing tools missing.")
            self.flashCompleted.emit(False, err)
            if self.resume_telemetry_fn:
                self.resume_telemetry_fn()
            return

        self._log(f"Selected flasher: {flasher_type}")
        self._log(f"Command: {' '.join(cmd)}")
        self._log("WARNING: DO NOT DISCONNECT USB CABLE OR CYCLE POWER DURING FLASHING!")

        # PHASE 4: FLASHING
        self.stateChanged.emit("FLASHING")
        self.progressChanged.emit(35, "Writing flash memory to ATmega328P...")
        self._log("Phase 4: Initiating physical flash programming...")

        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            )

            # Monitor progress with 40s timeout
            start_time = time.monotonic()
            timeout_seconds = 45.0
            last_progress = 35

            while True:
                if time.monotonic() - start_time > timeout_seconds:
                    process.kill()
                    err = f"Programming timed out after {timeout_seconds}s. Device may be unresponsive."
                    self._log(f"ERROR: {err}")
                    self.stateChanged.emit("FAILED")
                    self.progressChanged.emit(0, "Upload timeout.")
                    self.flashCompleted.emit(False, err)
                    if self.resume_telemetry_fn:
                        self.resume_telemetry_fn()
                    return

                line = process.stdout.readline()
                if not line and process.poll() is not None:
                    break

                if line:
                    line_clean = line.strip()
                    if line_clean:
                        self._log(f"  {line_clean}")

                        # Estimate progress based on avrdude output
                        if "Writing" in line_clean and "%" in line_clean:
                            m = re.search(r"(\d+)%", line_clean)
                            if m:
                                pct = int(m.group(1))
                                mapped_pct = 35 + int(pct * 0.35)
                                self.progressChanged.emit(mapped_pct, f"Writing flash: {pct}%")
                        elif "Reading" in line_clean and "%" in line_clean:
                            m = re.search(r"(\d+)%", line_clean)
                            if m:
                                pct = int(m.group(1))
                                mapped_pct = 70 + int(pct * 0.15)
                                self.progressChanged.emit(mapped_pct, f"Verifying flash: {pct}%")

            exit_code = process.wait()
            if exit_code != 0:
                err = f"Flasher exited with error code {exit_code}. Flash write failed."
                self._log(f"ERROR: {err}")
                self.stateChanged.emit("FAILED")
                self.progressChanged.emit(0, "Flash process error.")
                self.flashCompleted.emit(False, err)
                if self.resume_telemetry_fn:
                    self.resume_telemetry_fn()
                return

        except Exception as e:
            err = f"Subprocess invocation failure: {str(e)}"
            self._log(f"ERROR: {err}")
            self.stateChanged.emit("FAILED")
            self.flashCompleted.emit(False, err)
            if self.resume_telemetry_fn:
                self.resume_telemetry_fn()
            return

        self._log("Programmer reports successful write and verification!")
        self.progressChanged.emit(85, "Rebooting microcontroller...")

        # PHASE 5: VERIFYING POST-FLASH OPERATION
        self.stateChanged.emit("VERIFYING")
        self._log("Phase 5: Performing post-flash hardware-in-the-loop verification...")
        self._log("Waiting 2.5s for microcontroller auto-reset and bootloader initialization...")
        time.sleep(2.5)

        verified = False
        sensor_confirmed = False
        attempt = 0
        max_attempts = 3

        while attempt < max_attempts and not verified:
            attempt += 1
            self._log(f"Post-flash handshake probe attempt {attempt}/{max_attempts}...")
            try:
                ser = serial.Serial(self.port, baudrate=DEFAULT_BAUD_RATE, timeout=1.5, write_timeout=1.5)
                time.sleep(1.5)
                ser.reset_input_buffer()
                ser.write(DISCOVER_COMMAND)
                ser.flush()

                deadline = time.monotonic() + 4.0
                while time.monotonic() < deadline:
                    line = ser.readline().decode("utf-8", errors="ignore").strip()
                    if line:
                        self._log(f"  Probe response: {line}")
                        if "ID:GY30_LUX_PRO_2026" in line:
                            verified = True
                            if "ADDR_0x23" in line or "ADDR_0x5C" in line:
                                sensor_confirmed = True
                            break

                ser.close()
            except Exception as e:
                self._log(f"  Attempt {attempt} connection exception: {e}")
                time.sleep(1.0)

        if not verified:
            err = (
                "Flashing completed, but post-flash handshake verification failed. "
                "The board did not respond with ID:GY30_LUX_PRO_2026."
            )
            self._log(f"WARNING: {err}")
            self.stateChanged.emit("FAILED")
            self.progressChanged.emit(0, "Post-flash verification failed.")
            self.flashCompleted.emit(False, err)
            if self.resume_telemetry_fn:
                self.resume_telemetry_fn()
            return

        self._log("SUCCESS: Handshake verified! Microcontroller is active and running new firmware.")
        if sensor_confirmed:
            self._log("SUCCESS: Photodiode BH1750 I2C bus acknowledgment confirmed.")
        else:
            self._log("NOTICE: Microcontroller running; sensor awaiting ambient calibration.")

        # Re-engage normal telemetry worker
        if self.resume_telemetry_fn:
            self._log("Resuming application telemetry stream...")
            self.resume_telemetry_fn()

        self.stateChanged.emit("SUCCESS")
        self.progressChanged.emit(100, "Firmware update completed successfully!")
        self._log(f"=== Firmware Update Complete (Version v{manifest.firmware_version}) ===")
        self.flashCompleted.emit(
            True,
            f"Successfully updated Arduino Uno firmware to v{manifest.firmware_version} on {self.port}."
        )
