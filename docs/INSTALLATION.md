# LuxSense Pro — Installation & Deployment Guide

## 1. System Requirements
- **OS:** Windows 10 (Version 1809 or higher) / Windows 11 (64-bit)
- **Port:** Standard USB 2.0 or 3.0 Type-A/Type-C
- **Memory:** 512 MB RAM minimum (1 GB recommended)
- **Disk Storage:** 150 MB free disk space for program files and local telemetry SQLite database.

## 2. Installation Methods

### Method 1: Windows Setup Wizard (Recommended)
1. Download `LuxSense-Pro-Setup-v2.1.0.exe` from official GitHub Releases.
2. Verify the SHA-256 hash using PowerShell:
   ```powershell
   Get-FileHash LuxSense-Pro-Setup-v2.1.0.exe -Algorithm SHA256
   ```
3. Run the installer and complete the setup wizard.
4. The installer configures Start Menu shortcuts and registers the standalone updater bootstrapper (`updater.exe`).

### Method 2: Portable Distribution (.zip)
1. Download `LuxSense-Pro-v2.1.0-portable.zip`.
2. Extract the archive into any preferred directory (e.g. `C:\Tools\LuxSensePro\`).
3. Run `LuxSensePro.exe` directly without administrative elevation.

### Method 3: Silent Enterprise Deployment
For automated lab or domain deployment:
```cmd
LuxSense-Pro-Setup-v2.1.0.exe /VERYSILENT /SUPPRESSMSGBOXES /NORESTART /SP-
```

## 3. Post-Installation Verification
Upon first launch, navigate to **Settings & Update Center**:
1. Confirm installed version shows `v2.1.0`.
2. Select your preferred Update Channel: **Stable** or **Beta**.
3. Verify the sensor serial port under Hardware Interface.

