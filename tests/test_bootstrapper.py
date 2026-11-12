"""
Unit Tests for Updater Bootstrapper: Backup, Atomic Replacement, and Rollback
"""

import tempfile
import shutil
from pathlib import Path
from updater_bootstrapper.bootstrapper import create_backup, rollback

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

    # Clean up
    shutil.rmtree(temp_dir, ignore_errors=True)
