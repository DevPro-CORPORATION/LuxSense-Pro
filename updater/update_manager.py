"""
LuxSense Pro — GitHub Releases Update Manager
Queries GitHub Releases REST API, handles Stable & Beta update channels,
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

try:
    from PySide6.QtCore import QObject, QThread, Signal as pyqtSignal
except ImportError:
    from PyQt6.QtCore import QObject, QThread, pyqtSignal

from updater.manifest import ReleaseManifest, ReleaseAssetInfo, parse_sha256sums
from updater.security import compute_sha256, verify_sha256, verify_authenticode

GITHUB_OWNER = "DevPro-CORPORATION"
GITHUB_REPO = "LuxSense-Pro"
GITHUB_API_RELEASES_URL = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases"

def get_app_data_dir() -> Path:
    """Return standard user data directory for LuxSense Pro."""
    if sys.platform == "win32":
        base = os.environ.get("APPDATA") or os.path.expanduser("~\\AppData\\Roaming")
        data_dir = Path(base) / "DevPro" / "LuxSensePro"
    elif sys.platform == "darwin":
        data_dir = Path.home() / "Library" / "Application Support" / "DevPro" / "LuxSensePro"
    else:
        data_dir = Path.home() / ".config" / "devpro" / "luxsense-pro"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir

class UpdateCheckWorker(QThread):
    """Background worker to check GitHub Releases without blocking the UI."""
    check_completed = pyqtSignal(bool, object, str)  # update_available, release_dict, message
    check_error = pyqtSignal(str)

    def __init__(self, current_version: str, channel: str = "stable"):
        super().__init__()
        self.current_version = current_version
        self.channel = channel.lower()  # "stable" or "beta"

    def run(self):
        try:
            req = urllib.request.Request(
                GITHUB_API_RELEASES_URL,
                headers={
                    "User-Agent": f"LuxSensePro/{self.current_version}",
                    "Accept": "application/vnd.github.v3+json"
                }
            )
            try:
                with urllib.request.urlopen(req, timeout=12) as resp:
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
                self.check_completed.emit(False, None, "No releases published yet on GitHub.")
                return

            installed_ver = parse_version(self.current_version)
            best_release = None
            best_ver = None

            for r in releases:
                if r.get("draft", False):
                    continue

                is_pre = r.get("prerelease", False)
                tag = r.get("tag_name", "").lstrip("v")
                is_beta_tag = any(x in tag.lower() for x in ["beta", "alpha", "rc", "pre"])

                # In Stable channel, filter out all prereleases and beta tags
                if self.channel == "stable" and (is_pre or is_beta_tag):
                    continue

                try:
                    v = parse_version(tag)
                except Exception:
                    continue

                if best_ver is None or v > best_ver:
                    best_ver = v
                    best_release = r

            if not best_release or not best_ver:
                self.check_completed.emit(
                    False, None, f"No compatible release found for channel '{self.channel.upper()}'."
                )
                return

            # Downgrade prevention: published version must strictly exceed installed version
            if best_ver <= installed_ver:
                self.check_completed.emit(
                    False,
                    best_release,
                    f"LuxSense Pro is up to date (Installed: v{self.current_version}, Latest: {best_release.get('tag_name')})."
                )
                return

            # Update is available!
            self.check_completed.emit(
                True,
                best_release,
                f"New {self.channel.upper()} release available: v{best_ver} (Current: v{self.current_version})"
            )

        except Exception as e:
            self.check_error.emit(f"Unexpected update check error: {e}")

class DownloadWorker(QThread):
    """Background worker to download release assets with byte & percentage progress reporting."""
    progress = pyqtSignal(int, int, float)  # downloaded_bytes, total_bytes, percent
    finished = pyqtSignal(Path, str)        # downloaded_file_path, expected_sha256
    failed = pyqtSignal(str)

    def __init__(self, asset_url: str, filename: str, expected_sha256: str = "", current_version: str = "2.1.0"):
        super().__init__()
        self.asset_url = asset_url
        self.filename = filename
        self.expected_sha256 = expected_sha256
        self.current_version = current_version
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
                headers={"User-Agent": f"LuxSensePro/{self.current_version}"}
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
    Coordinates version checking, channel selection (Stable/Beta),
    download verification, and bootstrapper handover.
    """
    update_available = pyqtSignal(dict)       # Release data
    update_not_available = pyqtSignal(str)   # Status message
    update_error = pyqtSignal(str)           # Error message
    download_progress = pyqtSignal(int, int, float)
    ready_to_install = pyqtSignal(Path)
    verification_failed = pyqtSignal(str)

    def __init__(self, current_version: str = "2.1.0"):
        super().__init__()
        self.current_version = current_version
        self._check_worker: Optional[UpdateCheckWorker] = None
        self._download_worker: Optional[DownloadWorker] = None
        self.current_release_data: Optional[Dict[str, Any]] = None
        self.staged_installer_path: Optional[Path] = None

    def check_for_updates(self, channel: str = "stable"):
        """Starts asynchronous check for updates on the specified channel."""
        if self._check_worker and self._check_worker.isRunning():
            return

        self._check_worker = UpdateCheckWorker(current_version=self.current_version, channel=channel)
        self._check_worker.check_completed.connect(self._on_check_completed)
        self._check_worker.check_error.connect(self._on_check_error)
        self._check_worker.start()

    def _on_check_completed(self, is_available: bool, release_data: Optional[Dict[str, Any]], message: str):
        if is_available and release_data:
            self.current_release_data = release_data
            self.update_available.emit(release_data)
        else:
            self.update_not_available.emit(message)

    def _on_check_error(self, err_msg: str):
        self.update_error.emit(err_msg)

    def download_latest_installer(self):
        """Downloads the installer asset for the current active release data."""
        if self.current_release_data:
            self.start_download(self.current_release_data)
        else:
            self.update_error.emit("No release candidate available to download.")

    def find_installer_asset(self, release_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Finds Windows installer executable in release assets."""
        assets = release_data.get("assets", [])
        for asset in assets:
            name = asset.get("name", "").lower()
            if name.endswith(".exe") and ("setup" in name or "installer" in name):
                return asset
        for asset in assets:
            if asset.get("name", "").lower().endswith(".exe") and "updater" not in asset.get("name", "").lower():
                return asset
        return None

    def find_portable_asset(self, release_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Finds Windows portable zip archive in release assets."""
        assets = release_data.get("assets", [])
        for asset in assets:
            name = asset.get("name", "").lower()
            if name.endswith(".zip") and "portable" in name:
                return asset
        for asset in assets:
            if asset.get("name", "").lower().endswith(".zip"):
                return asset
        return None

    def start_download(self, release_data: Dict[str, Any]):
        """Downloads the installer asset with cryptographic verification."""
        installer_asset = self.find_installer_asset(release_data)
        if not installer_asset:
            self.update_error.emit("No Windows installer found in this release.")
            return

        download_url = installer_asset.get("browser_download_url")
        filename = installer_asset.get("name")
        expected_sha = ""

        # Extract SHA-256 hash from release body or manifest if present
        body = release_data.get("body", "")
        for line in body.splitlines():
            if filename in line and len(line) >= 64:
                for token in line.replace("`", " ").split():
                    if len(token) == 64 and all(c in "0123456789abcdefABCDEF" for c in token):
                        expected_sha = token.lower()
                        break
            if expected_sha:
                break

        # If not in body, resolve from SHA256SUMS.txt or release-manifest.json in release assets
        if not expected_sha:
            for a in release_data.get("assets", []):
                a_name = a.get("name", "").lower()
                a_url = a.get("browser_download_url", "")
                if a_name == "sha256sums.txt" and a_url:
                    try:
                        req = urllib.request.Request(
                            a_url,
                            headers={"User-Agent": f"LuxSensePro/{self.current_version}"}
                        )
                        with urllib.request.urlopen(req, timeout=10) as r:
                            sums_dict = parse_sha256sums(r.read().decode("utf-8", errors="replace"))
                            if filename in sums_dict:
                                expected_sha = sums_dict[filename]
                                break
                    except Exception:
                        pass
                elif a_name == "release-manifest.json" and a_url:
                    try:
                        req = urllib.request.Request(
                            a_url,
                            headers={"User-Agent": f"LuxSensePro/{self.current_version}"}
                        )
                        with urllib.request.urlopen(req, timeout=10) as r:
                            manifest = ReleaseManifest.from_json_str(r.read().decode("utf-8", errors="replace"))
                            if filename in manifest.assets:
                                expected_sha = manifest.assets[filename].sha256
                                break
                    except Exception:
                        pass

        self._download_worker = DownloadWorker(download_url, filename, expected_sha, self.current_version)
        self._download_worker.progress.connect(self.download_progress.emit)
        self._download_worker.finished.connect(self._verify_and_stage_update)
        self._download_worker.failed.connect(self.update_error.emit)
        self._download_worker.start()

    def _verify_and_stage_update(self, installer_path: Path, expected_sha: str):
        """Verifies binary integrity and Authenticode signature before permitting installation."""
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

        if sys.platform == "win32":
            valid, auth_msg = verify_authenticode(installer_path, expected_subject="DevPro")
            if "does not match expected" in auth_msg or "HashMismatch" in auth_msg:
                installer_path.unlink(missing_ok=True)
                self.verification_failed.emit(f"Authenticode Verification Failed: {auth_msg}")
                return

        self.staged_installer_path = installer_path
        self.ready_to_install.emit(installer_path)

    def launch_installer(self, installer_path: Optional[Any] = None, silent: bool = False, theme: str = "dark", new_version: str = "2.3.3"):
        """Executes dedicated native updater bootstrapper and terminates current LuxSense Pro instance."""
        target_path = installer_path or self.staged_installer_path
        if not target_path:
            self.update_error.emit("Installer file missing or not verified.")
            return

        if isinstance(target_path, str):
            target_path = Path(target_path)

        if not target_path.exists():
            self.update_error.emit(f"Installer binary not found at: {target_path}")
            return

        app_dir = Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path(__file__).resolve().parents[1]
        bootstrapper = app_dir / "updater.exe"
        if not bootstrapper.exists():
            bootstrapper = app_dir / "dist" / "updater.exe"

        current_pid = os.getpid()
        current_exe = sys.executable
        if not getattr(sys, 'frozen', False):
            candidate_exe = app_dir / "dist" / "LuxSensePro.exe"
            if candidate_exe.exists():
                current_exe = str(candidate_exe)

        # Resolve active user theme from storage
        try:
            from software.core.storage import UserSettings
            active_theme = UserSettings.load().theme or theme
        except Exception:
            active_theme = theme

        target_ver = new_version
        if self.current_release_data and self.current_release_data.get("tag_name"):
            target_ver = self.current_release_data.get("tag_name", "").lstrip("v")

        if bootstrapper.exists():
            args = [
                str(bootstrapper),
                "--installer", str(target_path),
                "--target-exe", str(current_exe),
                "--wait-pid", str(current_pid),
                "--theme", active_theme,
                "--old-version", self.current_version,
                "--new-version", target_ver
            ]
            if silent:
                args.append("--silent")
            subprocess.Popen(args, creationflags=subprocess.DETACHED_PROCESS if sys.platform == "win32" else 0)
        else:
            flags = ["/VERYSILENT", "/NORESTART"] if silent else []
            subprocess.Popen([str(target_path)] + flags)

        sys.exit(0)

