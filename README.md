# LuxSense Pro

**Enterprise-Grade Optical Radiometry & Real-Time Sensor Telemetry**  
*Official open-hardware and software instrument engineered by DevPro-CORP.*

---

## 1. Overview
LuxSense Pro is an optical metrology application paired with an **Arduino Uno R3** and **BH1750 (GY-30)** ambient light sensor. It acquires real-time illuminance readings (0.00 – 65,535.00 lx) over high-speed USB serial with rolling-128 XOR encrypted telemetry.

The application incorporates a complete GitHub-powered software update infrastructure under the **DevPro-CORP** organization (`DevPro-CORPORATION/luxsense-pro`). The desktop application independently checks GitHub for updates without requiring users to visit external websites.

- **GitHub Repository:** [https://github.com/DevPro-CORPORATION/luxsense-pro](https://github.com/DevPro-CORPORATION/luxsense-pro)
- **Official Distribution Channel:** GitHub Releases
- **Update Channels:** Stable (Production) & Beta (Previews)
- **Organization Ownership:** DevPro-CORP (`DevPro-CORPORATION`)

---

## 2. Repository Structure

In accordance with system specifications, the repository maintains the following structure:

```text
├── software/                 # Windows desktop application (PyQt6 interface & core)
│   ├── core/                 # Serial worker, storage, config, crypto packet
│   ├── ui/                   # Live monitor, analytics, calibration, settings & Update Center
│   └── main.py               # Main application entry point
├── firmware/                 # Arduino Uno C++ sketch & hardware specs
│   ├── LuxSense_Arduino/     # Official Arduino sketch (BH1750 driver + rolling XOR cipher)
│   └── README.md             # Hardware pinout table and wiring guide
├── installer/                # Windows installer packaging
│   ├── LuxSensePro_Setup.iss # Inno Setup 6 production installer script
│   └── build_installer.py    # Automated packaging pipeline (PyInstaller -> Inno Setup -> Checksums)
├── updater/                  # Update manager & standalone updater bootstrapper
│   ├── update_manager.py     # GitHub Releases API client with Stable/Beta channel filtering
│   ├── security.py           # SHA-256 hash calculation & Windows Authenticode validator
│   ├── manifest.py           # Release manifest and SHA256SUMS parser
│   ├── bootstrapper.py       # Standalone updater: PID wait, snapshot backup, rollback, relaunch
│   └── bootstrapper.spec     # PyInstaller compilation specification for updater.exe
├── docs/                     # Technical documentation
│   ├── ARCHITECTURE.md       # High-level architecture & telemetry pipeline
│   ├── INSTALLATION.md       # Setup wizard, portable mode, and enterprise deployment
│   ├── FIRMWARE_GUIDE.md     # Wiring schematic, I2C bus specs, and encryption details
│   ├── UPDATE_SYSTEM.md      # Update Center, Stable/Beta channels, SHA-256 & rollback
│   └── TROUBLESHOOTING.md    # USB driver fixes, COM port conflicts, and updater recovery
├── tests/                    # Automated test suite (pytest)
│   ├── test_bootstrapper.py  # Tests backup creation and automatic rollback
│   ├── test_security.py      # Tests SHA-256 verification and Authenticode validator
│   ├── test_serial_protocol.py # Tests rolling XOR decryption and checksum rejection
│   ├── test_storage.py       # Tests settings, calibration, and SQLite database
│   └── test_update_manager.py # Tests semver parsing, channel filtering, and downgrade prevention
├── .github/
│   ├── ISSUE_TEMPLATE/       # Standardized bug report and feature request templates
│   └── workflows/            # GitHub Actions CI/CD pipelines
│       ├── ci.yml            # Automated testing & firmware validation on push/PR
│       └── release.yml       # Production & beta release pipeline triggered on version tags
├── requirements.txt          # Python dependencies
├── CHANGELOG.md              # Semantic version history
└── LICENSE                   # DevPro-CORP Open Source License
```

---

## 3. In-App Update Center

Integrated directly into the **Settings** tab of LuxSense Pro:
- **Installed Version:** Displays currently running version (e.g. `v2.1.0`).
- **Latest Available Version:** Fetched asynchronously from GitHub Releases public REST API.
- **Update Channel Selector:**
  - `Stable (Official Releases)`: Filters out prerelease and beta builds. Only considers production releases.
  - `Beta (Prereleases & Previews)`: Includes preview builds, release candidates (`-rc*`), and beta tags (`-beta*`).
- **Release Notes:** Formatted markdown changelog for the discovered version.
- **Check for Updates Button:** Triggers an immediate scan on the selected channel.
- **Download Progress:** Real-time progress bar showing transferred MB / total MB and percentage.
- **Install Update Button:** Becomes active only after SHA-256 and digital signature verification pass.
- **Last Update Check:** Displays timestamp of the most recent check.

---

## 4. Secure Update Process

1. **GitHub Releases REST API:**
   Queries `https://api.github.com/repos/DevPro-CORPORATION/luxsense-pro/releases`.
   Never embeds write-access tokens.
2. **Semantic Versioning & Downgrade Prevention:**
   Compares versions using `packaging.version.Version`. Never downgrades automatically.
3. **Cryptographic SHA-256 Verification:**
   Hashes downloaded installer in 64 KB chunks and verifies against `release-manifest.json` / `SHA256SUMS.txt`. Corrupted or mismatched files are deleted immediately.
4. **Windows Authenticode Verification:**
   Inspects digital signature and confirms publisher subject matches `DevPro`.
5. **Standalone Updater Bootstrapper (`updater.exe`):**
   - Waits for parent PID to exit to avoid Windows file locks (`ERROR_SHARING_VIOLATION`).
   - Creates a timestamped directory backup (`LuxSensePro_backup_YYYYMMDD_HHMMSS`).
   - Executes installer.
   - If installation fails: Triggers automatic rollback, restores previous binaries, and relaunches the app.
   - If installation succeeds: Cleans up backup and launches the updated version.
6. **User Data Preservation:**
   All configuration (`settings.json`), calibration profiles (`calibration.json`), and measurement logs (`history.db`) reside in `%APPDATA%\DevPro\LuxSensePro\`. Upgrades and uninstalls leave this directory completely untouched.

---

## 5. GitHub Actions CI/CD Pipelines

- **CI Workflow (`.github/workflows/ci.yml`):**
  Runs automated tests (`pytest tests/`) and verifies Arduino sketch syntax on push/PR to `main`.
- **Release Workflow (`.github/workflows/release.yml`):**
  Triggered by tags matching `v*.*.*`:
  1. Runs automated tests (strict quality gate).
  2. Verifies firmware compilation syntax.
  3. Compiles application (`software/main.py`) with PyInstaller.
  4. Compiles standalone updater (`updater/bootstrapper.py`) with PyInstaller.
  5. Builds Windows setup wizard with Inno Setup 6.
  6. Packages portable ZIP distribution.
  7. Generates SHA-256 checksums (`SHA256SUMS.txt`, `release-manifest.json`).
  8. Publishes GitHub Release assets. Automatically sets `prerelease: true` for beta/rc tags and `prerelease: false` for stable tags.

---

## 6. Development & Verification

### Running Automated Tests
```powershell
.\.venv\Scripts\python.exe -m pytest tests/ -v
```

### Building Distribution Packages Locally
```powershell
.\.venv\Scripts\python.exe installer/build_installer.py
```
Outputs are compiled to `dist_installer/`:
- `LuxSense-Pro-Setup-v2.1.0.exe` (Windows Installer)
- `LuxSense-Pro-v2.1.0-portable.zip` (Portable Distribution)
- `release-manifest.json`
- `SHA256SUMS.txt`
