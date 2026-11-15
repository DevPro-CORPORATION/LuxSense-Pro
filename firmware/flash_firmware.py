"""
LuxSense Pro — Automated Arduino Uno Flashing Tool
Discovers connected Arduino Uno / CH340 / FTDI boards and flashes the compiled firmware.
"""

import sys
import subprocess
from pathlib import Path
import serial.tools.list_ports

def find_arduino_port():
    ports = serial.tools.list_ports.comports()
    for p in ports:
        desc = (p.description or "").lower()
        mfg = (p.manufacturer or "").lower()
        if "arduino" in desc or "ch340" in desc or "ftdi" in desc or "usb serial" in desc:
            return p.device
        if "arduino" in mfg:
            return p.device
    # If only one port found (excluding Bluetooth), return it
    valid = [p.device for p in ports if "bluetooth" not in (p.description or "").lower()]
    if valid:
        return valid[0]
    return None

def main():
    root_dir = Path(__file__).resolve().parents[1]
    arduino_cli = root_dir / "tools" / "arduino-cli" / "arduino-cli.exe"
    firmware_dir = root_dir / "firmware" / "LuxSense_Arduino"

    target_port = sys.argv[1] if len(sys.argv) > 1 else find_arduino_port()
    if not target_port:
        print("[Flash] Notice: No physical Arduino Uno detected on serial ports.")
        print("[Flash] When you plug in your Arduino Uno, specify the COM port:")
        print(f"        python firmware/flash_firmware.py COM5")
        return 1

    print(f"[Flash] Detected target port: {target_port}")
    if arduino_cli.exists():
        cmd = [
            str(arduino_cli), "upload",
            "-p", target_port,
            "--fqbn", "arduino:avr:uno",
            str(firmware_dir)
        ]
        print(f"[Flash] Executing: {' '.join(cmd)}")
        res = subprocess.run(cmd)
        if res.returncode == 0:
            print("[Flash] Successfully flashed LuxSense Pro firmware to Arduino Uno!")
            return 0
        else:
            print(f"[Flash] Flash command failed with code {res.returncode}")
            return res.returncode
    else:
        print(f"[Flash] Error: arduino-cli not found at {arduino_cli}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
