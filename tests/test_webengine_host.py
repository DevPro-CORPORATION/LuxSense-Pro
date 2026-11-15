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

def test_bridge_scientific_features():
    backend = BridgeBackend()

    # Uncertainty budget
    budget_json = backend.getUncertaintyBudget("default", 7.0)
    budget = json.loads(budget_json)
    assert "combined_standard_uncertainty" in budget
    assert "expanded_uncertainty_95" in budget

    # Exposure report
    exposure_json = backend.getExposureReport("default")
    exposure = json.loads(exposure_json)
    assert "cumulative_lux_hours" in exposure
    assert "cie157_conservation_status" in exposure

    # Spatial mapping
    backend.clearSpatialPoints("test_session")
    ok1 = backend.recordSpatialPoint("test_session", "P1", "Center", 0.0, 0.0, 500.0)
    ok2 = backend.recordSpatialPoint("test_session", "P2", "Corner", 1.0, 1.0, 420.0)
    assert ok1 and ok2

    pts_json = backend.getSpatialPoints("test_session")
    pts = json.loads(pts_json)
    assert len(pts) == 2

    uniformity_json = backend.getUniformityReport("test_session")
    uniformity = json.loads(uniformity_json)
    assert "uniformity_u1" in uniformity
    assert uniformity["points_count"] == 2

    # Session management
    ok_sess = backend.createExperimentSession(
        "sess_001", "Lab Chamber Trial", "Sarah Jenkins", "LED 4000K", 300.0, 750.0, "Testing cleanroom"
    )
    assert ok_sess is True

    sess_list = json.loads(backend.listExperimentSessions())
    assert any(s["session_id"] == "sess_001" for s in sess_list)

    # Scientific reports
    csv_rep = backend.exportScientificReport("sess_001", "csv")
    assert csv_rep.endswith(".csv")
    html_rep = backend.exportScientificReport("sess_001", "html")
    assert html_rep.endswith(".html")

    # Serial latency
    latency = backend.getSerialLatency()
    assert latency >= 0.0

def test_bridge_firmware_status_and_update_check():
    backend = BridgeBackend()
    fw_status_json = backend.getFirmwareStatus()
    fw_status = json.loads(fw_status_json)
    assert fw_status["board"] == "Arduino Uno R3"
    assert "ATmega328P" in fw_status["mcu"]
    assert "port" in fw_status

    check_res_json = backend.checkFirmwareUpdates()
    check_res = json.loads(check_res_json)
    assert "available" in check_res
    if check_res.get("available"):
        assert check_res["valid"] is True
        assert "manifest" in check_res

