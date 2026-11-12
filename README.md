# LuxSense Pro

**Enterprise-Grade Optical Radiometry & Real-Time Sensor Telemetry**  
*An official open-hardware and software instrument engineered by DevPro-CORP.*

---

## 1. Overview
LuxSense Pro is a precision photometric workstation application paired with an **Arduino Uno R3** and **BH1750 (GY-30)** digital illuminance sensor. It acquires real-time light intensity readings (0.00 – 65,535.00 lx) over high-speed USB serial protected by rolling-128 XOR encrypted telemetry.

The application incorporates a complete, secure GitHub-powered release and update system, Windows Authenticode publisher validation, safe rollback updater bootstrapper, and decoupled user state storage.

- **Official Product Portal:** [https://devpro-corporation.github.io/luxsense-pro/](https://devpro-corporation.github.io/luxsense-pro/)
- **GitHub Repository:** [https://github.com/DevPro-CORPORATION/luxsense-pro](https://github.com/DevPro-CORPORATION/luxsense-pro)
- **Organization Ownership:** DevPro-CORP (`DevPro-CORPORATION`)

---

## 2. Repository Architecture

```text
├── .github/
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug_report.md             # Standardized bug reporting form
│   │   └── feature_request.md        # Feature enhancement request form
│   └── workflows/
│       ├── ci.yml                    # Automated tests and verification on push/PR
│       └── release.yml               # GitHub Actions release build & publishing pipeline
├── app/                              # Desktop Application Package
│   ├── core/
│   │   ├── config.py                 # Application constants, paths, and version definitions
│   │   ├── crypto_packet.py          # 128-bit rolling-key XOR packet decoder & checksums
│   │   ├── serial_worker.py          # Arduino USB serial thread with auto-reconnect
│   │   └── storage.py                # Persistent user settings, calibration, SQLite history
│   ├── updater/
│   │   ├── manifest.py               # Release manifest and SHA256SUMS parser
│   │   ├── security.py               # SHA-256 hash calculation & Authenticode signature check
│   │   └── update_manager.py         # Asynchronous GitHub Releases API client & installer executor
│   ├── ui/
│   │   ├── analytics_tab.py          # Statistical telemetry view and CSV export
│   │   ├── calibration_tab.py        # Optical zero-offset and multiplier gain controls
│   │   ├── main_window.py            # Primary PyQt6 desktop interface
│   │   ├── monitor_tab.py            # Real-time digital gauge and packet indicators
│   │   ├── settings_tab.py           # Hardware config, update controls, data folder link
│   │   └── update_dialog.py          # Update notification modal with changelog and progress
│   └── main.py                       # Main application entry point
├── updater_bootstrapper/
│   ├── bootstrapper.py               # Standalone updater: backup, process wait, rollback
│   └── bootstrapper.spec             # PyInstaller spec for updater.exe
├── firmware/
│   ├── LuxSense_Arduino/
│   │   └── LuxSense_Arduino.ino      # Arduino Uno sketch with BH1750 driver and encryption
│   └── README.md                     # Hardware pinout, electrical specs, and wiring diagram
├── installer/
│   ├── LuxSensePro_Setup.iss         # Inno Setup 6 production installer configuration
│   └── build_installer.py            # Packaging pipeline: PyInstaller -> Inno Setup -> Manifests
├── website/                          # GitHub Pages Official Product Website
│   ├── index.html                    # 9-section scientific instrumentation website
│   ├── style.css                     # Graphite, ivory, and emerald green design system
│   ├── script.js                     # Dynamic GitHub Releases API sync with fallback
│   ├── releases.json                 # Embedded release manifest fallback
│   ├── assets/                       # SVG schematics, telemetry diagrams, and icons
│   └── docs/                         # Detailed installation and troubleshooting guides
├── tests/                            # Automated Unit & Integration Tests
│   ├── test_bootstrapper.py          # Tests backup creation and automatic rollback
│   ├── test_security.py              # Tests SHA-256 verification and Authenticode validator
│   ├── test_serial_protocol.py       # Tests rolling XOR decryption and checksum rejection
│   ├── test_storage.py               # Tests settings, calibration, and SQLite database
│   └── test_update_manager.py        # Tests semver parsing, downgrade prevention, manifests
├── requirements.txt                  # Python dependencies
├── CHANGELOG.md                      # Semantic version history
└── LICENSE                           # DevPro-CORP Open Source License
```

---

## 3. Automatic Update System

### A. Dynamic Semantic Versioning & Downgrade Prevention
- Queries the GitHub Releases public REST API (`/repos/DevPro-CORPORATION/luxsense-pro/releases`).
- Compares installed semver against published release tags via Python's `packaging.version.Version`.
- **Never downgrades automatically:** If `published_version <= installed_version`, the application reports that it is already up to date.
- Prerelease builds (`alpha`, `beta`, `rc`) are ignored by default unless the user enables *"Include preview and pre-release builds"* in Settings.

### B. Security Architecture
1. **No Embedded Write Tokens:** The application uses GitHub's public read-only Releases REST API.
2. **SHA-256 Checksum Validation:** The downloaded installer is hashed before execution. If the hash does not match `release-manifest.json` or `SHA256SUMS.txt`, the file is immediately deleted and the user is alerted.
3. **Windows Authenticode Verification:** The updater inspects the digital signature and verifies that the publisher matches DevPro-CORP.
4. **Never executes unverified files:** Execution is aborted if any cryptographic check fails.

### C. Standalone Updater Bootstrapper & Automatic Rollback
- Executable: `updater.exe`
- Process handover: Waits for the running LuxSense Pro PID to exit completely, avoiding Windows file-sharing locks (`ERROR_SHARING_VIOLATION`).
- Snapshot backup: Creates a timestamped directory backup of the current application files prior to installation.
- Failure recovery: If the installer exits with an error code or target files are missing, the bootstrapper automatically executes a full rollback, restores the previous version, and relaunches it.
- Seamless update: On success, temporary backups are cleaned up and the upgraded application is launched automatically.

### D. User State & Calibration Preservation
All user settings, custom zero-offset calibrations, gain multipliers, and historical SQLite readings reside in:
`%APPDATA%\DevPro\LuxSensePro\`
Application updates overwrite only application binaries, preserving all user data intact.

---

## 4. Hardware Architecture & Firmware

```
+--------------------+            I2C Bus            +--------------------+
|                    |  5V  ---------------------->  | VCC                |
|                    |  GND ---------------------->  | GND                |
|    Arduino Uno     |  A4 (SDA) <---------------->  | SDA   BH1750/GY-30 |
|    ATmega328P      |  A5 (SCL) ----------------->  | SCL                |
|                    |  GND ---------------------->  | ADDR (0x23)        |
+--------------------+                               +--------------------+
          |
          | USB Serial (115200 Baud)
          v
+--------------------+
|  Host Workstation  |
|  LuxSense Pro App  |
+--------------------+
```

- **Microcontroller:** Arduino Uno R3 (ATmega328P)
- **Sensor:** ROHM BH1750FVI (GY-30 module)
- **Communication:** I2C (Address `0x23`)
- **Telemetry Cipher:** 128-bit rolling-key XOR cipher (`SECRET_KEY[16]`) with modular checksum.

---

## 5. GitHub Actions Release Pipeline

The CI/CD pipeline (`.github/workflows/release.yml`) activates on tag pushes matching `v*.*.*`:
1. **Automated Testing:** Runs `pytest tests/` in a clean environment.
2. **PyInstaller Compilation:** Builds `LuxSensePro.exe` and `updater.exe`.
3. **Installer Packaging:** Builds `LuxSense-Pro-Setup-v{VERSION}.exe` with Inno Setup 6.
4. **Portable Packaging:** Packages `LuxSense-Pro-v{VERSION}-portable.zip`.
5. **Cryptographic Checksums:** Generates `SHA256SUMS.txt` and `release-manifest.json`.
6. **Release Publishing:** Publishes assets to GitHub Releases.
7. **Website Synchronization:** Deploys updated documentation and release manifests to GitHub Pages.

---

## 6. Official Product Website

The dedicated product website is hosted on GitHub Pages:
- **URL:** [https://devpro-corporation.github.io/luxsense-pro/](https://devpro-corporation.github.io/luxsense-pro/)
- Dynamically queries GitHub Releases to show live versions, changelogs, direct downloads, and SHA-256 checksums.
- Features graceful offline fallback to `releases.json`.
- 9 complete sections: Home, Features, Hardware, Software, Downloads, Release Notes, Documentation, Team, and About DevPro-CORP.

---

## 7. Development & Testing

### Running Tests
```bash
pytest tests/ -v
```

### Packaging Locally
```bash
python installer/build_installer.py
```

---

## 8. Team & Product Ownership

- **Product Ownership:** DevPro-CORP (DevPro Corporation)
- **M Somasundaram:** Lead Systems Architect & Founder
- **Alex Chen:** Embedded Systems & Firmware Engineer
- **Sarah Jenkins:** Photometric Metrology & Quality Lead
