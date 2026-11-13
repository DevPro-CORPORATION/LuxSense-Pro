"""
Unit Tests for User Settings, Calibration Profiles, and SQLite History Persistence
"""

import tempfile
from pathlib import Path
from software.core.storage import UserSettings, CalibrationProfile, MeasurementHistory

def test_calibration_profile_math():
    profile = CalibrationProfile(
        zero_offset=-2.5,
        gain_multiplier=1.05
    )
    raw_lux = 100.0
    calibrated = profile.apply(raw_lux)
    assert calibrated == 102.38

    dark_raw = 1.0
    dark_cal = profile.apply(dark_raw)
    assert dark_cal == 0.0

def test_settings_preservation():
    settings = UserSettings(
        serial_port="COM9",
        baud_rate=57600,
        update_channel="beta"
    )
    assert settings.serial_port == "COM9"
    assert settings.baud_rate == 57600
    assert settings.update_channel == "beta"

def test_measurement_history_db():
    history = MeasurementHistory()
    initial_count = history.get_count()
    history.add_reading(542.1, 550.0, 999, "COM_TEST")
    new_count = history.get_count()
    assert new_count == initial_count + 1

    recent = history.get_recent(limit=5)
    assert len(recent) > 0
    assert recent[0]["packet_id"] == 999
    assert recent[0]["port"] == "COM_TEST"
