"""
Unit Tests for Updater Bootstrapper: Backup, Atomic Replacement, and Rollback
"""

import tempfile
import shutil
from pathlib import Path
from updater.bootstrapper import create_backup, rollback, verify_package_sha256, run_headless_sync

def test_backup_and_rollback():
    temp_dir = Path(tempfile.mkdtemp())
    app_dir = temp_dir / "InstalledApp"
    app_dir.mkdir()
    (app_dir / "LuxSensePro.exe").write_text("VERSION_2_0_0_BIN")
    (app_dir / "config.dat").write_text("STABLE_CONFIG")

    # 1. Create backup
    backup_dir = create_backup(app_dir)
    assert backup_dir.exists()
    assert (backup_dir / "LuxSensePro.exe").read_text() == "VERSION_2_0_0_BIN"

    # 2. Simulate broken installation (corrupted files)
    (app_dir / "LuxSensePro.exe").write_text("CORRUPTED_BINARY")
    shutil.rmtree(app_dir / "config.dat", ignore_errors=True)

    # 3. Trigger rollback
    rollback(backup_dir, app_dir)

    # 4. Verify original files restored perfectly
    assert (app_dir / "LuxSensePro.exe").read_text() == "VERSION_2_0_0_BIN"
    assert (app_dir / "config.dat").read_text() == "STABLE_CONFIG"

    shutil.rmtree(temp_dir, ignore_errors=True)

def test_verify_package_sha256():
    temp_dir = Path(tempfile.mkdtemp())
    valid_pkg = temp_dir / "valid.exe"
    # Write at least 2KB
    valid_pkg.write_bytes(b"LUXSENSE_VALID_PACKAGE_PAYLOAD" * 100)

    ok, sha = verify_package_sha256(valid_pkg)
    assert ok is True
    assert len(sha) == 64

    # Truncated package
    short_pkg = temp_dir / "short.exe"
    short_pkg.write_bytes(b"SHORT")
    ok_short, msg = verify_package_sha256(short_pkg)
    assert ok_short is False
    assert "truncated" in msg.lower()

    # Missing package
    ok_missing, msg_missing = verify_package_sha256(temp_dir / "nonexistent.exe")
    assert ok_missing is False

    shutil.rmtree(temp_dir, ignore_errors=True)
