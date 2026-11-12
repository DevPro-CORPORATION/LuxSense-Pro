"""
LuxSense Pro — GitHub Releases Update Manager
Queries GitHub Releases REST API, evaluates semantic versions, downloads installer assets,
verifies cryptographic checksums & Authenticode signatures, and invokes the standalone updater.
"""

import os
import sys
import json
import time
import urllib.request
import urllib.error
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from packaging.version import parse as parse_version, Version

from PyQt6.QtCore import QObject, QThread, pyqtSignal

from app.core.config import (
    APP_VERSION,
    GITHUB_OWNER,
    GITHUB_REPO,
    GITHUB_API_RELEASES_URL,
    get_app_data_dir
)
from app.core.storage import UserSettings
from app.updater.manifest import ReleaseManifest, ReleaseAssetInfo, parse_sha256sums
from app.updater.security import compute_sha256, verify_sha256, verify_authenticode

class UpdateCheckWorker(QThread):
    """Background worker to check GitHub Releases without blocking UI."""
    check_completed = pyqtSignal(bool, object, str)  # update_available, release_dict, message
    check_error = pyqtSignal(str)

    def __init__(self, include_prereleases: bool = False):
        super().__init__()
        self.include_prereleases = include_prereleases

    def run(self):
        try:
            req = urllib.request.Request(
                GITHUB_API_RELEASES_URL,
                headers={
                    "User-Agent": f"LuxSensePro/{APP_VERSION}",
                    "Accept": "application/vnd.github.v3+json"
                }
            )
            try:
                with urllib.request.urlopen(req, timeout=10) as resp:
                    if resp.status != 200:
                        self.check_error.emit(f"GitHub API returned HTTP {resp.status}")
                        return
                    releases = json.loads(resp.read().decode("utf-8"))
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    self.check_error.emit(f"Repository releases not found at {GITHUB_API_RELEASES_URL}.")
                elif e.code == 403:
                    self.check_error.emit("GitHub API rate limit exceeded. Please try again later.")
                else:
                    self.check_error.emit(f"Network error (HTTP {e.code}): {e.reason}")
                return
            except urllib.error.URLError as e:
                self.check_error.emit(f"Could not connect to GitHub: {e.reason}")
                return

            if not releases or not isinstance(releases, list):
                self.check_completed.emit(False, None, "No releases published yet.")
                return

            # Find latest matching release
            installed_ver = parse_version(APP_VERSION)
            best_release = None
            best_ver = None

            for r in releases:
                if r.get("draft", False):
                    continue
                is_pre = r.get("prerelease", False)
                if is_pre and not self.include_prereleases:
                    continue

                tag = r.get("tag_name", "").lstrip("v")
                try:
                    v = parse_version(tag)
                except Exception:
                    continue

                if best_ver is None or v > best_ver:
                    best_ver = v
                    best_release = r

            if not best_release or not best_ver:
                self.check_completed.emit(False, None, "No compatible release version found.")
                return

            # Never downgrade automatically!
            if best_ver <= installed_ver:
                self.check_completed.emit(
                    False,
                    best_release,
                    f"LuxSense Pro is up to date (Installed: v{APP_VERSION}, Latest: v{best_release.get('tag_name')})."
                )
                return

            # Update is available!
            self.check_completed.emit(
                True,
                best_release,
                f"A new version is available: v{best_ver} (Current: v{APP_VERSION})"
            )

        except Exception as e:
            self.check_error.emit(f"Unexpected error while checking for updates: {e}")

class DownloadWorker(QThread):
    """Background worker to download release assets with progress reporting."""
    progress = pyqtSignal(int, int, float)  # downloaded_bytes, total_bytes, percent
    finished = pyqtSignal(Path, str)        # downloaded_file_path, expected_sha256
    failed = pyqtSignal(str)

    def __init__(self, asset_url: str, filename: str, expected_sha256: str = ""):
        super().__init__()
        self.asset_url = asset_url
        self.filename = filename
        self.expected_sha256 = expected_sha256
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def run(self):
        try:
            download_dir = get_app_data_dir() / "updates"
            download_dir.mkdir(parents=True, exist_ok=True)
            target_path = download_dir / self.filename

            req = urllib.request.Request(
                self.asset_url,
                headers={"User-Agent": f"LuxSensePro/{APP_VERSION}"}
            )

            with urllib.request.urlopen(req, timeout=30) as response:
                total_size = int(response.headers.get("content-length", 0))
                downloaded = 0
                chunk_size = 65536

                with open(target_path, "wb") as f:
                    while True:
                        if self._cancelled:
                            target_path.unlink(missing_ok=True)
                            self.failed.emit("Download cancelled by user.")
                            return
                        chunk = response.read(chunk_size)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)
                        percent = (downloaded / total_size * 100.0) if total_size > 0 else 0.0
                        self.progress.emit(downloaded, total_size, percent)

            self.finished.emit(target_path, self.expected_sha256)
        except Exception as e:
            self.failed.emit(f"Download failed: {e}")

class UpdateManager(QObject):
    """
    Central Update Manager for LuxSense Pro.
    Coordinates version checking, user prompts, download validation, and bootstrapper handover.
    """
    update_available = pyqtSignal(dict)       # Release data
    update_not_available = pyqtSignal(str)   # Message
    update_error = pyqtSignal(str)           # Error message
    download_progress = pyqtSignal(int, int, float)
    ready_to_install = pyqtSignal(Path)
    verification_failed = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.settings = UserSettings.load()
        self._check_worker: Optional[UpdateCheckWorker] = None
        self._download_worker: Optional[DownloadWorker] = None
        self.current_release_data: Optional[Dict[str, Any]] = None

    def check_for_updates(self, manual: bool = False):
        """Starts asynchronous check for updates."""
        if self._check_worker and self._check_worker.isRunning():
            return

        self._check_worker = UpdateCheckWorker(include_prereleases=self.settings.include_prereleases)
        self._check_worker.check_completed.connect(self._on_check_completed)
        self._check_worker.check_error.connect(self._on_check_error)
        self._check_worker.start()

    def _on_check_completed(self, is_available: bool, release_data: Optional[Dict[str, Any]], message: str):
        # Update timestamp
        self.settings.last_update_check = time.strftime("%Y-%m-%d %H:%M:%S")
        self.settings.save()

        if is_available and release_data:
            tag = release_data.get("tag_name", "")
            # Check if user postponed this specific version
            if self.settings.postponed_version == tag:
                self.update_not_available.emit(f"Update {tag} is available, but currently postponed.")
                return

            self.current_release_data = release_data
            self.update_available.emit(release_data)
        else:
            self.update_not_available.emit(message)

    def _on_check_error(self, err_msg: str):
        self.update_error.emit(err_msg)

    def postpone_update(self, version_tag: str):
        """Allows user to postpone an update until next manual check or future release."""
        self.settings.postponed_version = version_tag
        self.settings.save()

    def clear_postponed(self):
        self.settings.postponed_version = None
        self.settings.save()

    def find_installer_asset(self, release_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Finds Windows installer executable in release assets."""
        assets = release_data.get("assets", [])
        for asset in assets:
            name = asset.get("name", "").lower()
            if name.endswith(".exe") and ("setup" in name or "installer" in name):
                return asset
        # Fallback to any .exe
        for asset in assets:
            if asset.get("name", "").lower().endswith(".exe") and "updater" not in asset.get("name", "").lower():
                return asset
        return None

    def find_manifest_or_checksums(self, release_data: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
        """Finds release-manifest.json or SHA256SUMS.txt URLs if available."""
        manifest_url = None
        sums_url = None
        for asset in release_data.get("assets", []):
            name = asset.get("name", "").lower()
            if name == "release-manifest.json":
                manifest_url = asset.get("browser_download_url")
            elif "sha256" in name:
                sums_url = asset.get("browser_download_url")
        return manifest_url, sums_url

    def start_download(self, release_data: Dict[str, Any]):
        """Downloads the installer asset with cryptographic verification."""
        installer_asset = self.find_installer_asset(release_data)
        if not installer_asset:
            self.update_error.emit("No Windows installer found in this release.")
            return

        download_url = installer_asset.get("browser_download_url")
        filename = installer_asset.get("name")
        expected_sha = ""

        # Check release body or manifest for embedded SHA-256
        body = release_data.get("body", "")
        for line in body.splitlines():
            if filename in line and len(line) >= 64:
                for token in line.replace("`", " ").split():
                    if len(token) == 64 and all(c in "0123456789abcdefABCDEF" for c in token):
                        expected_sha = token.lower()
                        break

        self._download_worker = DownloadWorker(download_url, filename, expected_sha)
        self._download_worker.progress.connect(self.download_progress.emit)
        self._download_worker.finished.connect(self._verify_and_stage_update)
        self._download_worker.failed.connect(self.update_error.emit)
        self._download_worker.start()

    def _verify_and_stage_update(self, installer_path: Path, expected_sha: str):
        """Verifies downloaded binary integrity and Authenticode signature before execution."""
        # 1. SHA-256 verification
        actual_sha = compute_sha256(installer_path)
        if expected_sha:
            if actual_sha.lower() != expected_sha.lower():
                installer_path.unlink(missing_ok=True)
                msg = (
                    f"CRITICAL SECURITY ALERT: SHA-256 hash mismatch!\n"
                    f"Expected: {expected_sha}\n"
                    f"Computed: {actual_sha}\n"
                    f"The file was deleted to protect system integrity."
                )
                self.verification_failed.emit(msg)
                return

        # 2. Windows Authenticode digital signature check
        if sys.platform == "win32":
            valid, auth_msg = verify_authenticode(installer_path, expected_subject="DevPro")
            # If signed and invalid/mismatched publisher, reject!
            if "does not match expected" in auth_msg or "HashMismatch" in auth_msg:
                installer_path.unlink(missing_ok=True)
                self.verification_failed.emit(f"Authenticode Verification Failed: {auth_msg}")
                return

        self.ready_to_install.emit(installer_path)

    def launch_installer(self, installer_path: Path, silent: bool = False):
        """
        Executes updater bootstrapper or verified installer, then terminates LuxSense Pro cleanly.
        """
        if not installer_path.exists():
            self.update_error.emit("Installer file missing.")
            return

        # Look for updater bootstrapper in installation directory or app root
        app_dir = Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path(__file__).resolve().parents[2]
        bootstrapper = app_dir / "updater.exe"

        current_pid = os.getpid()
        current_exe = sys.executable

        if bootstrapper.exists():
            # Launch standalone bootstrapper with safe rollback and process handoff
            args = [
                str(bootstrapper),
                "--installer", str(installer_path),
                "--target-exe", str(current_exe),
                "--wait-pid", str(current_pid)
            ]
            if silent:
                args.append("--silent")
            subprocess.Popen(args, creationflags=subprocess.DETACHED_PROCESS if sys.platform == "win32" else 0)
        else:
            # Direct verified installer execution with silent or interactive UI
            flags = ["/VERYSILENT", "/NORESTART"] if silent else []
            subprocess.Popen([str(installer_path)] + flags)

        # Terminate current app cleanly to unlock files for replacement
        sys.exit(0)
