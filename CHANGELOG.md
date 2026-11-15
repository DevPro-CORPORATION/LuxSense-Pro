# LuxSense Pro — Changelog

All notable changes to LuxSense Pro are documented in this file.
Version formatting follows [Semantic Versioning](https://semver.org/).

## [2.3.1] - 2026-11-15

### Added
- **Multi-Board AVR Flashing Support:** Extended the Firmware Update Center and security validation engine to support both Arduino Uno R3 and Arduino Nano (ATmega328P 16MHz) hardware targets, including dynamic FQBN configuration and baud rate selection.
- **Dynamic Spectral Chart Theming:** Bound the Technical Info photopic responsivity comparison chart (BH1750 vs. CIE 1931 V(λ)) to dynamic theme changes, rendering crystal-clear light-mode typography, borders, and gradients.
- **Portable Release Asset Resolver:** Added `find_portable_asset()` to the update subsystem for direct automated discovery and extraction of standalone portable distributions.
- **Firmware Security Compatibility Test Suite:** Added unit tests verifying cross-board ATmega328P compatibility between Uno and Nano targets.

### Fixed
- **Serial Worker Shutdown Latency:** Re-ordered `SerialWorker.stop()` to close the active COM port prior to calling `wait()`, eliminating a 2-second blocking delay during disconnect and shutdown.
- **Light Mode Contrast Consistency:** Eliminated hardcoded dark backgrounds (`bg-zinc-800/80`, `bg-zinc-700`) in the disconnected hardware banner, mapping theme-aware variables and adding light-mode styling for secondary text classes.
- **Updater Bootstrapper Directory Collisions:** Configured `dirs_exist_ok=True` in `updater/bootstrapper.py` backup creation and rollback mechanisms to prevent Windows `FileExistsError` during locked file recovery.
- **UserSettings Theme Validation:** Added post-initialization dataclass normalization to ensure corrupted or unexpected theme settings gracefully fallback to supported profiles (`dark`, `light`, `system`).

## [2.3.0] - 2026-11-15

### Added
- **Dedicated Hardware Setup Workspace:** Complete interactive schematic connecting Arduino Uno R3 to GY-30 (BH1750), 5-point pre-flight checklist, engineering electrical specifications, and architecture clarification separating USB programming from I²C runtime telemetry.
- **Appearance Settings & Full Dual Theming:** Complete high-contrast Clean Metrology Light mode, Precision Dark mode, and Windows System Default with live preview cards, persistent configuration in `%APPDATA%`, and automatic OS theme synchronization.
- **Apache ECharts Theme Adaptation:** Seamless dynamic palette switching for dual-axis optical transfer curves, frequency distribution histograms, and real-time photodiode streaming charts without flicker.
- **Subsystem POST Startup Sequence:** Genuine four-stage asynchronous subsystem initialization verifying IPC bridge, metrology tables, hardware discovery, and UI readiness with measurable progress and fail-safe timeout bypass.
- **Microcontroller Hardware Programming Controls:** Integrated board selector (Arduino Uno R3 / ATmega328P), firmware target selector (v2.0.0 official signed microcode vs v1.2.0 legacy), and dedicated COM port scan and selector directly inside the Firmware Update Center.
- **Seamless In-App Update Flow:** Maintained `updater.exe` strictly as an internal background installation helper, removing external website download confusion while preserving pre-update backup, cryptographic verification, and rollback recovery.
- **Unified Software & Physical Firmware Update Architecture:** Complete update architecture bridging the high-level Windows application and physical Arduino Uno (ATmega328P) microcontroller firmware.
- **Ed25519 Cryptographic Microcode Signing:** Asymmetric signature verification for all microcontroller payloads with embedded public key and SHA-256 binary validation.
- **Dedicated ATmega328P Firmware Update Center:** Embedded sub-tab in Settings with real-time MCU status, 32 KB flash memory gauge, signature verification badges, and live diagnostic terminal.
- **Strict Opt-In Firmware Security:** Microcontroller flashing requires explicit operator authorization via confirmation checkboxes; software updates never trigger automated flashing.
- **Safe 5-Phase Flashing State Machine:** Pre-flight cryptographic check -> graceful telemetry teardown -> serial port release -> programmer execution (`arduino-cli` / `avrdude`) -> post-flash bootloader delay -> handshake query (`ID:GY30_LUX_PRO_2026`) & BH1750 I2C probe -> telemetry resumption.
- **Bootloader Recovery Documentation & In-App Guide:** Clear documentation of ATmega328P 32 KB single-bank memory constraints, Optiboot 1.5s power-cycle recovery window, and 6-pin ICSP header recovery.
- **Dynamic In-App Update Center:** Dynamic version discovery via `getAppVersion()` bridge call, explicit "LuxSense Pro is up to date" banners, detailed error alerts with retry capabilities, and automatic release asset manifest checksum lookup.
- **Comprehensive Upgrade Lifecycle Test Suite:** Added end-to-end tests for version detection, download failure cleanup, SHA-256 mismatch rejection, and bootstrapper rollback.

### Fixed
- **Update Center Invocation Slots:** Fixed argument signature mismatch between JavaScript frontend and Qt WebChannel backend for `checkForUpdates`, `downloadUpdate`, and `installUpdate`.
- **Silent Update Failures:** Resolved issue where update errors failed to notify the UI, leaving the update check in a perpetual loading state.
- **Website Production Alignment:** Updated official website hero section, download center, SHA-256 checksums, and documentation tabs to reflect the verified v2.3.0 release.

## [2.2.0] - 2026-11-15

### Added
- **Native Windows Titlebar Controls:** Enforced standard Windows native titlebar controls through PySide6 `QMainWindow` with complete Win32 window manager integration (Aero Snap, taskbar pinning, Alt+Tab icon, native drag/resize).
- **Sampling Rate Synchronization:** Updated live oscillogram buffer sizing and UI copy to reflect the physical BH1750 4.0 Hz acquisition rate (250ms interval).
- **Memory Leak Mitigation:** Added explicit unmount cleanup hooks (`dispose()` and `ResizeObserver.disconnect()`) across Apache ECharts instances.

### Fixed
- **Metrology Zero-Fabrication Guardrail:** Eradicated artificial `520.0 lx` fallback in `ScientificWorkspace.tsx`. If physical hardware is disconnected or unreadable, the system displays an explicit warning and refuses data entry.
- **Typography Polish:** Replaced raw LaTeX math `$V(\lambda)$` with clean Unicode `V(λ)` in `TeamWorkspace.tsx`. Corrected corporate subtitle typography.

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
