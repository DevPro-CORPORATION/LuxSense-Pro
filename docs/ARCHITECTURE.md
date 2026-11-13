# LuxSense Pro — System Architecture

## 1. Architectural Overview
LuxSense Pro is an enterprise-grade photometric sensing workstation application engineered by DevPro-CORP. It acquires real-time light intensity measurements (0.00 – 65,535.00 lx) from an **Arduino Uno R3** and **BH1750 (GY-30)** sensor over USB serial.

```text
+--------------------------------------------------------------+
|                    Hardware Layer (Firmware)                 |
|  Arduino Uno R3 (ATmega328P)  <--I2C (0x23)--> BH1750 Sensor |
|  - 115200 Baud UART Serial                                   |
|  - 128-Bit Rolling-Key XOR Cipher Packet Stream              |
+--------------------------------------------------------------+
                               |
                               | USB Serial (COMx)
                               v
+--------------------------------------------------------------+
|                 Software Layer (LuxSense Pro)                |
|  - PyQt6 High-Contrast Scientific Interface                  |
|  - SerialWorker Thread (Handshake & XOR Packet Decryptor)    |
|  - Photometric Calibration Engine (Dark Offset & Gain)       |
|  - SQLite Persistent Telemetry Storage                       |
+--------------------------------------------------------------+
                               |
                               | GitHub Releases REST API
                               v
+--------------------------------------------------------------+
|                 Update & Release Subsystem                   |
|  - In-App Update Center (Settings Tab)                       |
|  - Update Channels: Stable (Production) & Beta (Previews)    |
|  - Dual Verification: SHA-256 Digest & Windows Authenticode  |
|  - Standalone Updater Bootstrapper (Process Wait & Rollback) |
+--------------------------------------------------------------+
```

## 2. Directory Structure

```text
├── software/                 # Windows desktop application package
│   ├── core/                 # Serial worker, storage, config, crypto packet
│   └── ui/                   # PyQt6 interface, monitor, analytics, settings & Update Center
├── firmware/                 # Arduino Uno C++ sketch & hardware specs
├── installer/                # Inno Setup 6 packaging & build pipeline
├── updater/                  # Standalone updater bootstrapper & update manager
├── docs/                     # Comprehensive technical documentation
├── tests/                    # Automated test suite (pytest)
└── .github/workflows/        # CI/CD pipelines for testing, building, and publishing
```

## 3. Persistent User State Decoupling
To ensure zero data loss during software upgrades or uninstallation, all personal user state is decoupled from program files and stored in standard Windows AppData:
`%APPDATA%\DevPro\LuxSensePro\`
- `settings.json`: User preferences, active update channel (`stable` or `beta`), port, baud rate, and check timestamps.
- `calibration.json`: Photometric zero-offset and optical gain multiplier.
- `history.db`: SQLite database storing historical sensor readings with packet sequence numbers.

