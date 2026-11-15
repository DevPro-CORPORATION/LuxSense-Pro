# LuxSense Pro — Continuous In-App Update Architecture

**Document Version:** 2.1.0-PRODUCTION  
**Date:** November 15, 2026  
**Publisher:** DevPro-CORP  
**Module:** Update Center & Standalone Bootstrapper Pipeline

---

## 1. Update Architecture Philosophy

LuxSense Pro delivers seamless software updates through an integrated, in-app Update Center. The primary engineering goals are:
1. **Single Initial Installation:** Users install LuxSense Pro once. All future features and bugfixes are delivered via in-app updates without requiring a manual download or complete reinstall.
2. **Zero Data Loss Guarantee:** User settings, dark-offset/gain calibration profiles, and historical SQLite measurements are decoupled from application binaries and are 100% preserved across updates.
3. **Atomic Execution & Automatic Rollback:** Updates are executed by a dedicated external bootstrapper process (`updater.exe`). If an installation is interrupted or fails verification, the updater automatically rolls back to the previous working installation.
4. **Firmware Decoupling:** Hardware firmware updates remain completely independent and require explicit, intentional user initiation. The updater **never** automatically flashes connected Arduino microcontrollers.

---

## 2. In-App Update Center Workflow

```
[GitHub Releases REST API]
            │
            ▼
[UpdateCheckWorker (QThread)] ── Channel Filtering (Stable / Beta)
            │
            ▼
[Update Center UI (React)] ── Displays Version, Changelog & Download Button
            │  (User confirms download)
            ▼
[DownloadWorker (QThread)] ── Downloads to %APPDATA%/updates/ with byte progress
            │
            ▼
[Cryptographic Verification] ── SHA-256 verification against release-manifest.json
            │  (User confirms installation)
            ▼
[Handover to updater.exe] ── Main app closes; bootstrapper waits for PID exit
            │
            ├──> Step 1: Create timestamped backup of current installation
            ├──> Step 2: Execute verified Inno Setup installer silently
            ├──> Step 3: Verify exit code == 0
            │       ├── [SUCCESS] ──> Launch updated LuxSensePro.exe
            │       └── [FAILURE] ──> Execute rollback() from backup directory
```

---

## 3. Cryptographic Verification & Security Guardrails

### A. SHA-256 Integrity Verification
- Release assets are accompanied by `release-manifest.json` and `SHA256SUMS.txt`.
- Before any binary is executed, `updater.security.verify_sha256()` computes the SHA-256 hash of the downloaded installer in 64 KB chunks and verifies an exact match.
- Unverified, corrupted, or truncated files are immediately deleted from disk.

### B. Authenticode Publisher Verification
- `updater.security.verify_authenticode()` queries the Windows Win32 `WinVerifyTrust` API or PowerShell `Get-AuthenticodeSignature` to confirm publisher authenticity.
- Self-signed test builds and production-signed binaries are validated before execution.

### C. Channel Filtering & Downgrade Prevention
- **Stable Channel:** Strictly filters out prereleases, release candidates, and tags containing `beta`, `alpha`, or `rc`.
- **Beta Channel:** Allows early-adopter access to feature release candidates.
- **Downgrade Guardrail:** The updater parses semantic versions using `packaging.version`. If `published_ver <= installed_ver`, the update is blocked, preventing accidental downgrades.

---

## 4. Standalone Bootstrapper Lifecycle (`updater.exe`)

Because Windows locks executing `.exe` and `.dll` files in memory, an active application cannot overwrite its own executable. `updater.exe` resolves this:

1. **Process Wait Loop:** Queries Win32 `OpenProcess(SYNCHRONIZE, ...)` on the parent application PID. Waits up to 15 seconds for clean termination.
2. **Pre-Update Backup:** Deep-copies the current application directory to:
   `%LOCALAPPDATA%\Programs\DevPro\LuxSense Pro_backup_YYYYMMDD_HHMMSS`
3. **Silent Installation:** Invokes the installer with `/VERYSILENT /SUPPRESSMSGBOXES /NORESTART /SP-`.
4. **Failure Recovery:** If the installer exits with a non-zero code, `updater.exe` deletes the corrupted directory and restores the full directory from the backup before alerting the user.

---

## 5. Firmware Independence Policy

Microcontroller hardware carries physical flash memory wear limits (typically 10,000 to 100,000 write cycles) and risk of communication failure during flashing.

**Policy:**
- Application updates **never** flash or modify the connected microcontroller.
- Firmware updates are distributed as documented Arduino sketches in the `firmware/` directory and can only be uploaded intentionally by the user via the Firmware Management interface.
