# LuxSense Pro — GitHub Update Infrastructure

## 1. Overview
LuxSense Pro contains an automated update infrastructure driven directly by GitHub Releases under the DevPro-CORP organization (`DevPro-CORPORATION/luxsense-pro`).

Users can independently check for updates, inspect release notes, download verified packages, and trigger automated upgrades from the **Update Center** in the Settings tab without visiting external web pages.

---

## 2. In-App Update Center Features

The Update Center is embedded in **Settings & Update Center**:
- **Installed Version:** Displays the currently running semantic version (e.g. `v2.1.0`).
- **Latest Available Version:** Dynamically updated from the GitHub Releases REST API.
- **Update Channel Selector:**
  - `Stable (Official Releases)`: Filters out all prerelease and beta builds. Only considers production-ready releases.
  - `Beta (Prereleases & Previews)`: Includes preview builds, release candidates (`-rc*`), and beta tags (`-beta*`).
- **Release Notes:** Formatted markdown changelog for the discovered release.
- **Check for Updates Button:** Initiates an asynchronous query against GitHub Releases.
- **Download Progress:** Live progress bar displaying downloaded bytes, total payload size, and percentage.
- **Install Update Button:** Enabled only after SHA-256 and Authenticode verification succeed.
- **Last Update Check:** Displays formatted timestamp of the most recent check.

---

## 3. Secure Update Architecture

```text
+-----------------------+
|  GitHub Releases API  |  Query public releases endpoint
+-----------------------+
           |
           v
+-----------------------+
|   Update Manager      |  1. Parse semantic versions (packaging.version)
| (software/updater)    |  2. Enforce channel filtering (Stable vs Beta)
|                       |  3. Prevent automated downgrades
+-----------------------+
           |
           v
+-----------------------+
|   Download Worker     |  Stream installer payload to %APPDATA%\...\updates\
+-----------------------+
           |
           v
+-----------------------+
|   Security Engine     |  1. Compute 64KB chunked SHA-256 digest
|                       |  2. Compare with release-manifest.json / SHA256SUMS.txt
|                       |  3. Verify Windows Authenticode digital signature
|                       |  * Corrupted or mismatched files deleted immediately *
+-----------------------+
           |
           v
+-----------------------+
|  User Confirmation    |  Explicit prompt before executing installation
+-----------------------+
           |
           v
+-----------------------+
| Standalone Updater    |  1. Wait for parent LuxSensePro.exe PID to terminate
| (updater/bootstrapper)|  2. Create timestamped snapshot backup of app directory
|                       |  3. Run verified installer in silent mode
|                       |  4. On failure: Execute rollback & relaunch previous version
|                       |  5. On success: Clean up backup & launch new version
+-----------------------+
```

---

## 4. Recovery & Rollback Mechanism

Windows file-locking (`ERROR_SHARING_VIOLATION`) prevents an executable from replacing itself while running. LuxSense Pro solves this with an isolated bootstrapper executable:

1. **Process Wait (`--wait-pid <PID>`):** The updater monitors the parent process handle until it exits completely.
2. **Snapshot Backup:** Creates `LuxSensePro_backup_YYYYMMDD_HHMMSS` containing all previous binaries.
3. **Execution & Health Check:** Executes the installer. If the installer returns non-zero or the target binary is missing, `rollback()` is triggered immediately.
4. **Restoration:** Restores the previous binaries from the backup snapshot and relaunches the stable version, ensuring the workstation is never left non-operational.
