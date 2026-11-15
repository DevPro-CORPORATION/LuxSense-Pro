"""
Unit & Integration Tests for LuxSense Pro Post-Update Changelog Experience
Verifies:
1. First launch / clean install does not trigger the changelog modal.
2. Version upgrade (e.g. 2.3.0 -> 2.3.1) properly triggers the changelog card.
3. Changelog acknowledgement is persisted in settings.json and never displays repeatedly.
4. Failed updates or rollbacks (e.g. 2.3.1 -> 2.3.0) do not display the changelog card.
5. Subsequent upgrades (e.g. 2.3.1 -> 2.3.2) trigger the changelog card again.
6. WebEngine bridge slots (checkPendingChangelog, acknowledgeUpdate) return valid JSON and update state.
"""

import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from software.core.storage import UserSettings, is_newer_version, APP_VERSION
from software.core.webengine_host import BridgeBackend

@pytest.fixture
def isolated_settings(tmp_path, monkeypatch):
    """Isolate settings directory so tests do not touch active user data."""
    data_dir = tmp_path / "DevPro" / "LuxSensePro"
    data_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr("software.core.storage.get_app_data_dir", lambda: data_dir)
    return data_dir

def test_version_comparison_logic():
    """Verify semantic and packaging version comparison."""
    assert is_newer_version("2.3.1", "2.3.0") is True
    assert is_newer_version("2.3.1", "2.3.1") is False
    assert is_newer_version("2.3.0", "2.3.1") is False
    assert is_newer_version("3.0.0", "2.3.1") is True
    assert is_newer_version("2.3.1", None) is False
    assert is_newer_version("", "2.3.1") is False

def test_first_launch_does_not_show_changelog(isolated_settings):
    """On brand new clean installation, changelog card must NOT show."""
    settings_file = isolated_settings / "settings.json"
    assert not settings_file.exists()

    settings = UserSettings.load()
    assert settings.last_acknowledged_version == APP_VERSION
    assert settings.previous_version is None
    assert settings.should_show_changelog() is False
    assert settings_file.exists()

def test_repeated_launch_same_version(isolated_settings):
    """Repeated launches of the same installed version must NOT repeat changelog."""
    # First launch
    settings = UserSettings.load()
    assert settings.should_show_changelog() is False

    # Second launch
    settings2 = UserSettings.load()
    assert settings2.last_acknowledged_version == APP_VERSION
    assert settings2.previous_version is None
    assert settings2.should_show_changelog() is False

def test_upgrade_triggers_changelog_experience(isolated_settings):
    """Upgrading from an older version (e.g. 2.3.0) triggers changelog card."""
    settings_file = isolated_settings / "settings.json"
    with open(settings_file, "w", encoding="utf-8") as f:
        json.dump({
            "serial_port": "COM5",
            "last_acknowledged_version": "2.3.0",
            "theme": "dark"
        }, f)

    settings = UserSettings.load()
    assert settings.last_acknowledged_version == "2.3.0"
    assert settings.previous_version == "2.3.0"
    assert settings.should_show_changelog() is True

def test_acknowledgement_persists_and_prevents_retrigger(isolated_settings):
    """Acknowledging an update saves the new version and clears pending changelog."""
    settings_file = isolated_settings / "settings.json"
    with open(settings_file, "w", encoding="utf-8") as f:
        json.dump({
            "last_acknowledged_version": "2.3.0",
            "theme": "dark"
        }, f)

    settings = UserSettings.load()
    assert settings.should_show_changelog() is True

    # User acknowledges changelog
    settings.acknowledge_version(APP_VERSION)
    assert settings.last_acknowledged_version == APP_VERSION
    assert settings.previous_version is None
    assert settings.should_show_changelog() is False

    # Relaunch application
    reloaded = UserSettings.load()
    assert reloaded.last_acknowledged_version == APP_VERSION
    assert reloaded.previous_version is None
    assert reloaded.should_show_changelog() is False

def test_failed_update_or_rollback_never_shows_changelog(isolated_settings, monkeypatch):
    """If a rollback occurs (e.g. user reverts from 2.3.3 to 2.3.2), do NOT show changelog."""
    settings_file = isolated_settings / "settings.json"
    # User had previously acknowledged 2.3.3
    with open(settings_file, "w", encoding="utf-8") as f:
        json.dump({
            "last_acknowledged_version": "2.3.3",
            "theme": "dark"
        }, f)

    # Simulate running an older binary (v2.3.2)
    monkeypatch.setattr("software.core.storage.APP_VERSION", "2.3.2")

    settings = UserSettings.load()
    assert settings.last_acknowledged_version == "2.3.3"
    assert settings.previous_version is None
    assert settings.should_show_changelog() is False

def test_subsequent_upgrade_triggers_again(isolated_settings, monkeypatch):
    """A subsequent future upgrade (e.g. 2.3.2 -> 2.3.3) triggers the changelog again."""
    settings_file = isolated_settings / "settings.json"
    with open(settings_file, "w", encoding="utf-8") as f:
        json.dump({
            "last_acknowledged_version": "2.3.2",
            "theme": "dark"
        }, f)

    # Simulate running future binary (v2.3.3)
    monkeypatch.setattr("software.core.storage.APP_VERSION", "2.3.3")

    settings = UserSettings.load()
    assert settings.last_acknowledged_version == "2.3.2"
    assert settings.previous_version == "2.3.2"
    assert settings.should_show_changelog() is True

def test_webengine_bridge_changelog_slots(isolated_settings, monkeypatch):
    """Verify BridgeBackend.checkPendingChangelog and acknowledgeUpdate slots."""
    settings_file = isolated_settings / "settings.json"
    with open(settings_file, "w", encoding="utf-8") as f:
        json.dump({
            "last_acknowledged_version": "2.3.0",
            "theme": "dark"
        }, f)

    backend = BridgeBackend(auto_connect=False)
    
    # 1. Query pending changelog
    res_raw = backend.checkPendingChangelog()
    res = json.loads(res_raw)
    assert res["show"] is True
    assert res["previous_version"] == "2.3.0"
    assert res["current_version"] == APP_VERSION
    assert len(res["categories"]) >= 3

    # 2. Acknowledge changelog
    ack_res = backend.acknowledgeUpdate(APP_VERSION)
    assert ack_res is True

    # 3. Query again: must return show = False
    res2_raw = backend.checkPendingChangelog()
    res2 = json.loads(res2_raw)
    assert res2["show"] is False
