# LuxSense Pro — Windows Platform Compatibility Specification

**Document Version:** 2.1.0-PRODUCTION  
**Date:** November 15, 2026  
**Publisher:** DevPro-CORP  
**Target Environments:** Windows 10 (22H2 64-bit) & Windows 11 (64-bit)

---

## 1. Operating System Compatibility Matrix

| Operating System | Architecture | Supported | Status | Verification & Technical Details |
|:---|:---|:---:|:---:|:---|
| **Windows 11 (24H2 / Build 26100)** | x86_64 (64-bit) | **YES** | **VERIFIED PASS** | Tested directly on physical host silicon. Application launch, QtWebEngine GPU rendering, and COM5 USB serial communication verified. |
| **Windows 11 (23H2 / 22H2 / 21H2)** | x86_64 (64-bit) | **YES** | **SUPPORTED** | Shares identical Win32 kernel, Universal C Runtime (UCRT), and `usbser.sys` CDC-ACM serial stack as Build 26100. |
| **Windows 10 (22H2 / Build 19045)** | x86_64 (64-bit) | **YES** | **SUPPORTED** | Fully supported target. Chromium 118+ embedded in QtWebEngine and PySide6 requires Windows 10 1809 or later. |
| **Windows 10 (pre-1809)** | x86_64 (64-bit) | **NO** | **UNSUPPORTED** | Lacks modern Chromium Core Sandbox and UCRT features required by Qt 6.8. |
| **Windows 7 / 8 / 8.1** | Any | **NO** | **UNSUPPORTED** | Deprecated by Microsoft and unsupported by Chromium/QtWebEngine 6. Installation blocked by Inno Setup OS version check. |
| **Windows 32-bit (x86)** | 32-bit | **NO** | **UNSUPPORTED** | QtWebEngine dropped 32-bit Windows binary support in Qt 6.x. Installer targets 64-bit exclusively. |
| **Windows 11 on ARM64** | ARM64 | **YES (Emulated)**| **SUPPORTED** | Runs via Windows 11 ARM64 built-in x64 emulation layer with USB serial passthrough. |

---

## 2. Standard User Privilege Architecture (Non-Admin Operation)

LuxSense Pro is designed with enterprise-grade least-privilege security principles:

1. **Zero Administrator Requirement for Normal Operation:**
   - The installer uses `PrivilegesRequired=lowest` with `PrivilegesRequiredOverridesAllowed=dialog`.
   - Default user installation path: `%LOCALAPPDATA%\Programs\DevPro\LuxSense Pro`.
   - Per-machine administrator installation is optional (`/ALLUSERS`).
2. **User Data Isolation:**
   - Configuration (`settings.json`), calibration profiles (`calibration.json`), and the SQLite telemetry store (`luxsense.db`) are decoupled from program binaries and reside in `%APPDATA%\DevPro\LuxSensePro\`.
   - Normal users have full read/write permissions to their user profile without UAC prompts.
3. **In-App Updates without UAC Prompts:**
   - Because the application is installed in user scope (`%LOCALAPPDATA%`), the standalone updater (`updater.exe`) executes updates, file replacements, and backups without triggering Windows User Account Control (UAC) elevation prompts.

---

## 3. High-DPI Display Scaling & Multi-Monitor Handling

LuxSense Pro incorporates Qt 6 High-DPI scaling features paired with responsive CSS styling:

- **Per-Monitor DPI v2 Awareness:**
  - Automatic adaptation to mixed-DPI setups (e.g., 4K primary display at 150% scaling and 1080p secondary display at 100%).
  - Vector icon rendering (SVG via Lucide React) ensures zero icon pixelation across all scaling steps (100%, 125%, 150%, 175%, 200%).
- **Fluid Layout Boundaries:**
  - Minimum application window size: `1120 x 740 px`.
  - Default window size: `1280 x 840 px`.
  - Responsive flexbox/grid layout ensures all instrument panels remain accessible at resolutions ranging from 1366x768 to 3840x2160 (4K).
- **Reduced Motion Accessibility:**
  - Respects Windows OS Accessibility settings (`System > Accessibility > Visual effects > Animation effects`).
  - Automatically suppresses cinematic POST animations and transitions when reduced motion is preferred by the operating system.

---

## 4. USB Serial & Microcontroller Hardware Communication

### Driver Requirements
1. **Official Arduino Uno R3 (ATmega16U2 USB-to-UART bridge):**
   - Uses Microsoft standard USB Communication Device Class (CDC-ACM) driver (`usbser.sys`).
   - Included out-of-the-box in all Windows 10 (1809+) and Windows 11 installations. No third-party driver download needed.
   - Identified by USB Hardware ID: `USB\VID_2341&PID_0043`.
2. **Third-Party Arduino Clones (CH340 / CP2102 / FT232):**
   - CH340 / CH341: Requires WCH CH341SER Windows driver (frequently pre-installed via Windows Update).
   - CP2102: Requires Silicon Labs CP210x VCP driver (inbox on Windows 11).
   - FT232: Uses Microsoft-certified FTDI CDM driver.

### COM Port Auto-Detection & Enumeration
- The application automatically scans COM ports from `COM1` to `COM256` using `serial.tools.list_ports`.
- Initiates automated handshake `DISCOVER_LUX_SENSOR` with baud rates up to `115200`.
- Sub-2ms round-trip latency verified across hardware communication loops.

---

## 5. Known Limitations & Technical Constraints

1. **Simultaneous Port Access:**
   - Windows grants exclusive lock to serial COM ports. If another application (e.g., Arduino IDE Serial Monitor or PuTTY) is connected to `COM5`, LuxSense Pro will enter `DISCONNECTED` state until the other application releases the port.
2. **Virtual Machine COM Passthrough:**
   - When running inside Hyper-V, VMware, or VirtualBox, the host USB device must be redirected to the guest OS for physical hardware acquisition.
