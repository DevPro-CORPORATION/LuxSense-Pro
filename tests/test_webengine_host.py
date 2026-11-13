"""
Tests for Qt WebEngine Bridge Backend
Verifies IPC slots, calibration serialization, and update payload formats.
"""

import json
import pytest
from software.core.webengine_host import BridgeBackend

def test_bridge_backend_init():
    backend = BridgeBackend()
    assert backend.settings is not None
    assert backend.calibration is not None
    assert backend.history is not None
    assert backend.update_mgr is not None

def test_bridge_scan_ports():
    backend = BridgeBackend()
    ports_json = backend.scanPorts()
    ports = json.loads(ports_json)
    assert isinstance(ports, list)
    assert len(ports) >= 1

def test_bridge_calibration_roundtrip():
    backend = BridgeBackend()
    cal_json = backend.getCalibration()
    cal = json.loads(cal_json)
    assert "gain_multiplier" in cal
    assert "zero_offset" in cal

    # Update calibration
    ok = backend.saveCalibration(2.5, 1.15, "Automated Metrology Test")
    assert ok is True

    updated_json = backend.getCalibration()
    updated = json.loads(updated_json)
    assert updated["zero_offset"] == 2.5
    assert updated["gain_multiplier"] == 1.15
    assert updated["notes"] == "Automated Metrology Test"

def test_bridge_settings_roundtrip():
    backend = BridgeBackend()
    settings_json = backend.getSettings()
    settings = json.loads(settings_json)
    assert "update_channel" in settings
    assert settings["update_channel"] in ["stable", "beta"]

    settings["update_channel"] = "beta"
    settings["serial_port"] = "COM9"
    ok = backend.saveSettings(json.dumps(settings))
    assert ok is True

    reloaded = json.loads(backend.getSettings())
    assert reloaded["update_channel"] == "beta"
    assert reloaded["serial_port"] == "COM9"

def test_bridge_telemetry_history_and_csv():
    backend = BridgeBackend()
    history_json = backend.getTelemetryHistory(10)
    records = json.loads(history_json)
    assert isinstance(records, list)

    csv_path = backend.exportHistoryCsv()
    assert csv_path.endswith(".csv")
