# LuxSense Pro — Changelog

All notable changes to LuxSense Pro are documented in this file.
Version formatting follows [Semantic Versioning](https://semver.org/).

## [2.1.0] - 2026-11-12

### Added
- **Automatic Desktop Updates:** Direct GitHub Releases REST API integration comparing local and remote semantic versions.
- **Cryptographic Security Layer:** Automatic SHA-256 checksum verification against release manifests and Windows Authenticode publisher checks.
- **Independent Updater Bootstrapper:** Dedicated process handoff (`updater.exe`) with pre-update backup creation and automated rollback recovery on failure.
- **Settings & Update Controls:** New Settings tab with manual "Check for Updates" button, startup auto-check toggle, and prerelease channel option.
- **Persistent User Storage:** Decoupled user configuration, photometric calibration profiles, and historical measurements into `%APPDATA%\DevPro\LuxSensePro\`.
- **Photometric Calibration:** Dark-offset and linear gain adjustments with live equation previews.
- **Historical Telemetry Database:** SQLite persistent storage with aggregate calculations (min, max, avg) and CSV export.
- **CI/CD Automation:** GitHub Actions workflows for automated testing, PyInstaller binary compilation, Inno Setup packaging, release publishing, and GitHub Pages sync.
- **Official Product Website:** Dedicated GitHub Pages responsive portal with live release synchronization and documentation.

## [2.0.0] - 2026-11-10

### Added
- Initial LuxSense Pro interface with PyQt6 live illuminance readout.
- Arduino Uno USB serial communication with BH1750 ambient light sensor.
- Rolling-128 XOR telemetry encryption and modular checksum verification.
