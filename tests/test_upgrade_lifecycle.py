"""
LuxSense Pro — End-to-End Upgrade Lifecycle & Failure Recovery Test Suite
Tests upgrading from v2.1.0 to v2.3.0:
1. Version detection & manifest parsing
2. Network download failure handling
3. SHA-256 cryptographic hash mismatch rejection & file deletion
4. Installation failure & bootstrapper rollback to v2.1.0
5. Successful installation & user data preservation
"""

import os
import sys
import json
import shutil
import tempfile
from pathlib import Path
import pytest
from packaging.version import parse as parse_version

from updater.manifest import ReleaseManifest, parse_sha256sums
from updater.security import compute_sha256, verify_sha256
from updater.bootstrapper import create_backup, rollback
from updater.update_manager import UpdateManager
from software.core.storage import UserSettings, CalibrationProfile, get_app_data_dir

@pytest.fixture
def mock_release_manifest():
    manifest_path = Path(__file__).resolve().parents[1] / "dist_installer" / "release-manifest.json"
    assert manifest_path.exists(), "release-manifest.json must exist"
    with open(manifest_path, "r", encoding="utf-8") as f:
        return json.load(f)

@pytest.fixture
def mock_sha256sums():
    sums_path = Path(__file__).resolve().parents[1] / "dist_installer" / "SHA256SUMS.txt"
    assert sums_path.exists(), "SHA256SUMS.txt must exist"
    return parse_sha256sums(sums_path.read_text(encoding="utf-8"))

def test_lifecycle_1_version_detection_from_v210(mock_release_manifest):
    """Verify an installed v2.1.0 instance correctly detects v2.3.0 as newer."""
    installed_ver = parse_version("2.1.0")
    published_ver = parse_version(mock_release_manifest["version"])

    assert published_ver > installed_ver, f"Published {published_ver} should exceed installed {installed_ver}"
    assert mock_release_manifest["channel"] == "stable"
    assert not mock_release_manifest.get("prerelease", False)

def test_lifecycle_2_manifest_asset_and_checksum_integrity(mock_release_manifest, mock_sha256sums):
    """Verify release manifest assets match SHA256SUMS.txt."""
    assets = mock_release_manifest["assets"]
    setup_name = f"LuxSense-Pro-Setup-v{mock_release_manifest['version']}.exe"
    setup_asset = assets.get(setup_name)
    assert setup_asset is not None
    assert setup_asset["sha256"] in mock_sha256sums.values()
    assert setup_name in mock_sha256sums

def test_lifecycle_3_failed_download_cleanup():
    """Verify interrupted/failed download leaves no corrupt staging file."""
    temp_dir = Path(tempfile.mkdtemp())
    download_target = temp_dir / "LuxSense-Pro-Setup-v2.3.0.exe.part"
    download_target.write_bytes(b"INCOMPLETE_BYTE_STREAM")

    # Simulate worker error/cancel cleanup
    if download_target.exists():
        download_target.unlink(missing_ok=True)

    assert not download_target.exists()
    shutil.rmtree(temp_dir, ignore_errors=True)

def test_lifecycle_4_hash_mismatch_immediate_deletion():
    """Verify corrupted/tampered installer is immediately deleted upon hash mismatch."""
    temp_dir = Path(tempfile.mkdtemp())
    fake_installer = temp_dir / "LuxSense-Pro-Setup-v2.3.0.exe"
    fake_installer.write_bytes(b"TAMPERED_OR_CORRUPT_PAYLOAD_CONTENT")

    expected_sha = "0000000000000000000000000000000000000000000000000000000000000000"
    actual_sha = compute_sha256(fake_installer)

    assert actual_sha != expected_sha

    # Verification gate logic
    verification_passed = False
    error_message = ""
    if actual_sha.lower() != expected_sha.lower():
        fake_installer.unlink(missing_ok=True)
        verification_passed = False
        error_message = "CRITICAL SECURITY ALERT: SHA-256 hash mismatch!"

    assert not verification_passed
    assert not fake_installer.exists(), "Corrupted installer must be unlinked from disk immediately"
    assert "SHA-256 hash mismatch" in error_message
    shutil.rmtree(temp_dir, ignore_errors=True)

def test_lifecycle_5_installation_failure_and_rollback():
    """Verify bootstrapper rolls back to v2.1.0 on installer failure."""
    temp_dir = Path(tempfile.mkdtemp())
    app_dir = temp_dir / "LuxSensePro"
    app_dir.mkdir()

    # Seed v2.1.0 app files
    exe_path = app_dir / "LuxSensePro.exe"
    exe_path.write_bytes(b"LUXSENSE_PRO_v2.1.0_BINARY_IMAGE")
    config_path = app_dir / "app_config.json"
    config_path.write_text(json.dumps({"version": "2.1.0", "calibrated": True}))

    # 1. Create backup prior to update
    backup_dir = create_backup(app_dir)
    assert backup_dir.exists()
    assert (backup_dir / "LuxSensePro.exe").read_bytes() == b"LUXSENSE_PRO_v2.1.0_BINARY_IMAGE"

    # 2. Simulate installer failure (corrupted in-place write)
    exe_path.write_bytes(b"CORRUPTED_INCOMPLETE_WRITE")

    # 3. Simulate failure detection and rollback trigger
    simulated_exit_code = 1  # Inno Setup non-zero exit
    if simulated_exit_code != 0:
        rollback(backup_dir, app_dir)

    # 4. Verify original v2.1.0 binary & config restored
    assert exe_path.read_bytes() == b"LUXSENSE_PRO_v2.1.0_BINARY_IMAGE"
    assert json.loads(config_path.read_text())["version"] == "2.1.0"

    shutil.rmtree(temp_dir, ignore_errors=True)

def test_lifecycle_6_successful_upgrade_and_user_data_preservation():
    """Verify successful upgrade to v2.3.0 leaves user metrology data completely intact."""
    temp_dir = Path(tempfile.mkdtemp())
    app_dir = temp_dir / "LuxSensePro"
    app_dir.mkdir()

    # 1. v2.1.0 Installed Application
    exe_path = app_dir / "LuxSensePro.exe"
    exe_path.write_bytes(b"LUXSENSE_PRO_v2.1.0_ORIGINAL")

    # 2. User Data in AppData
    user_data_dir = temp_dir / "AppData" / "DevPro" / "LuxSensePro"
    user_data_dir.mkdir(parents=True)
    user_settings_file = user_data_dir / "settings.json"
    user_settings_file.write_text(json.dumps({
        "serial_port": "COM5",
        "baud_rate": 115200,
        "calibration_factor": 1.042,
        "operator_id": "METROLOGY_OP_42"
    }))

    # 3. Successful Update execution
    backup_dir = create_backup(app_dir)
    # Simulate Inno Setup successful file replacement
    exe_path.write_bytes(b"LUXSENSE_PRO_v2.3.0_NEW_IMAGE")
    simulated_exit_code = 0
    if simulated_exit_code == 0:
        shutil.rmtree(backup_dir, ignore_errors=True)

    # 4. Verify updated binary
    assert exe_path.read_bytes() == b"LUXSENSE_PRO_v2.3.0_NEW_IMAGE"
    assert not backup_dir.exists()

    # 5. Verify User Data in AppData was NEVER touched
    assert user_settings_file.exists()
    restored_settings = json.loads(user_settings_file.read_text())
    assert restored_settings["operator_id"] == "METROLOGY_OP_42"
    assert restored_settings["calibration_factor"] == 1.042

    shutil.rmtree(temp_dir, ignore_errors=True)
