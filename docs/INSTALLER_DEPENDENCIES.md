# LuxSense Pro — Complete Installer Dependency & Bundling Audit

**Document Version:** 2.1.0-PRODUCTION  
**Date:** November 15, 2026  
**Publisher:** DevPro-CORP  
**Scope:** Standalone Windows Installer (`LuxSense-Pro-Setup-v2.1.0.exe`) and Portable Distribution

---

## 1. Zero-Prerequisite Architecture Guarantee

LuxSense Pro is delivered as a 100% self-contained Windows application. End users are **never required** to install:
- Python or pip environments.
- Node.js, npm, or JavaScript build tools.
- Qt libraries or PySide6 packages.
- Microsoft Visual C++ redistributable packages manually (required UCRT DLLs are packaged inside).
- Git, AGY agent harnesses, or developer tooling.

The application operates completely decoupled from source trees, virtual environments, and developer-specific filesystem paths.

---

## 2. Bundled Component Inventory

The production installer packages the following subsystems into independent compiled executables:

| Subsystem / Library | Version | Bundling Method | Purpose & Responsibility |
|:---|:---:|:---:|:---|
| **Python Runtime Engine** | 3.15.0 (64-bit) | Embedded PyInstaller bootloader | Executes hardware daemon, calibration engine, and IPC bridge. |
| **PySide6 Qt Shell** | 6.8.x | Embedded dynamic libraries | High-performance Windows application frame and window management. |
| **QtWebEngine Core & Widgets** | Chromium 118+ | Embedded Chromium engine | Renders the React + TypeScript user interface with hardware acceleration. |
| **QtWebChannel Bridge** | 6.8.x | Native Qt IPC | Bidirectional C++/Python to JavaScript bridge (`window.backend`). |
| **React + TypeScript Frontend** | React 18.3.1 | Compiled static bundle in `datas` | Zero-latency UI with Framer Motion, GSAP, and Apache ECharts. |
| **PySerial Communication** | 3.5 | Embedded Python package | Direct CDC-ACM serial communication with Arduino ATmega328P. |
| **SQLite3 Database Engine** | 3.45+ | Native C library (`sqlite3.dll`) | Immutable telemetry logging, spatial surveys, and session management. |
| **Microsoft Visual C++ Runtime** | 14.x / UCRT | Bundled DLLs | `vcruntime140.dll`, `vcruntime140_1.dll`, `msvcp140.dll` bundled inside. |
| **Inno Setup Engine** | 6.7.3 | Self-extracting setup bootloader | LZMA2 compressed installer with silent mode and uninstallation registry. |
| **Standalone Updater** | 2.1.0 | Independent binary (`updater.exe`) | Out-of-process file replacement, backup, and atomic rollback manager. |

---

## 3. Path Decoupling & Relocatable Execution Audit

The application strictly implements frozen-binary path detection:

```python
if getattr(sys, 'frozen', False):
    # Running inside standalone PyInstaller bundle
    base_dir = Path(getattr(sys, '_MEIPASS', Path(sys.executable).parent))
else:
    # Running in development environment
    base_dir = Path(__file__).resolve().parents[1]

# User data is ALWAYS decoupled into the standard Windows APPDATA directory
app_data = Path(os.environ.get("APPDATA")) / "DevPro" / "LuxSensePro"
```

### Filesystem Isolation Guarantee:
- **Application Binaries:** Installed into `%LOCALAPPDATA%\Programs\DevPro\LuxSense Pro\` (or custom user directory).
- **User Data & Settings:** Stored strictly in `%APPDATA%\DevPro\LuxSensePro\`:
  - `settings.json` (user preferences and update channel)
  - `calibration.json` (sensor calibration coefficients)
  - `luxsense.db` (SQLite measurement history)
  - `updates/` (staging directory for downloaded release installers)

Uninstalling or updating the application **never** destroys user measurements or calibration profiles.

---

## 4. Binary Footprint & Checksum Verification

```text
Asset: LuxSense-Pro-Setup-v2.1.0.exe
Size: 221,878,110 bytes (~211.6 MB)
SHA-256: 90ca74381124291c3e2bca241ed5c494c2e2f4f834aa592e26701c1d32595616

Asset: LuxSense-Pro-v2.1.0-portable.zip
Size: 230,613,274 bytes (~219.9 MB)
SHA-256: f9a290e9bc85880f5d83738bc582db6f4542668d1706a926a461f8ac5bece7b1

Asset: updater.exe
Size: 9,396,954 bytes (~8.9 MB)
SHA-256: e789441b9c006b9151f982ec3a669b45c70e4f6b4afb0d8cc1a3a23d28b57d74
```
