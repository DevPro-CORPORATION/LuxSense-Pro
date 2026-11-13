# LuxSense Pro — Diagnostic & Troubleshooting Guide

## 1. Hardware & Serial Communication Issues

### Symptom: Serial Port Not Found
- **Cause:** Device not enumerated by Windows or missing USB-to-UART bridge driver.
- **Fix:**
  1. Open Windows Device Manager (`Win + X` -> Device Manager).
  2. Inspect **Ports (COM & LPT)**.
  3. If *USB-SERIAL CH340* appears with a warning sign, install the official WCH CH341SER driver.
  4. If using genuine Arduino Uno, drivers are in `C:\Program Files (x86)\Arduino\drivers\`.
  5. Click **Scan Ports** in the LuxSense Pro Settings tab.

### Symptom: PermissionError: [Errno 13] Access is denied: 'COMx'
- **Cause:** Another process is holding the serial port open.
- **Fix:** Close Arduino IDE Serial Monitor, Cura, PuTTY, or other serial monitors before launching LuxSense Pro.

### Symptom: Handshake Verification Timeout
- **Cause:** Arduino Uno reboot cycle or baud rate mismatch.
- **Fix:**
  - Arduino Uno auto-resets when the DTR line toggles upon port connection. The desktop app pauses 2.0 seconds to allow the bootloader to hand off to sketch execution.
  - Verify that the sketch baud rate in `LuxSense_Arduino.ino` matches the Baud Rate setting in the desktop app (default `115200`).

---

## 2. Update Infrastructure Diagnostics

### Diagnostic Logs
The standalone updater bootstrapper logs events to:
`%TEMP%\luxsense_pro_updater.log`

Inspect the log file via PowerShell:
```powershell
Get-Content "$env:TEMP\luxsense_pro_updater.log" -Tail 50
```

### Error: SHA-256 Checksum Mismatch
- **Cause:** Network packet loss or incomplete download payload.
- **Safety Action:** LuxSense Pro automatically deletes the corrupted installer file from `%APPDATA%\DevPro\LuxSensePro\updates\` to prevent execution of unverified binaries.
- **Fix:** Check network connection and click **Check for Updates** again.

### Error: Update Rollback Triggered
- **Cause:** Installer encountered an error (e.g. insufficient privileges or disk space).
- **Safety Action:** The bootstrapper automatically restored your previous version and relaunched it. No manual recovery is needed.
- **Fix:** Verify disk space in `C:\Program Files (x86)\DevPro\LuxSense Pro\` or run as administrator.

