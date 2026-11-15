"""
Unit Tests for LuxSense Pro Firmware Flasher
Tests flashing tool discovery, state machine transitions, invalid package rejection,
port verification failure handling, and simulated flashing workflows.
"""

import tempfile
from pathlib import Path
import pytest
from unittest.mock import MagicMock, patch

from software.core.firmware_flasher import (
    find_arduino_cli,
    find_avrdude,
    FirmwareFlashWorker
)
from software.core.firmware_security import FirmwareManifest, compute_file_sha256

@pytest.fixture
def valid_firmware(tmp_path):
    hex_path = tmp_path / "firmware.hex"
    hex_path.write_text(":100000000C945C000C946E000C946E000C946E0012\n:00000001FF\n")

    from tests.conftest import get_test_signing_key
    priv = get_test_signing_key()
    sha = compute_file_sha256(hex_path)
    manifest = FirmwareManifest(
        firmware_version="2.0.0",
        release_name="LuxSense Pro Microcode v2.0.0",
        published_at="2026-11-15T15:30:00Z",
        target_board="arduino:avr:uno",
        target_mcu="atmega328p",
        bootloader="optiboot",
        baud_rate=115200,
        clock_mhz=16,
        supported_sensors=["BH1750 (0x23)"],
        min_app_version="2.0.0",
        hex_filename=hex_path.name,
        hex_sha256=sha,
        hex_size=hex_path.stat().st_size,
        release_notes="Unit test firmware",
        publisher="DevPro-CORP Root Authority",
        signature=""
    )
    manifest.signature = priv.sign(manifest.canonical_bytes()).hex()
    return hex_path, manifest.__dict__

def test_tool_discovery():
    cli = find_arduino_cli()
    avrdude, avrdude_conf = find_avrdude()
    if cli is None and avrdude is None:
        pytest.skip("Neither arduino-cli nor avrdude discovered in headless CI runner.")
    assert cli is not None or avrdude is not None

def test_flasher_security_rejection_prevents_hardware_touch(valid_firmware):
    hex_path, manifest_data = valid_firmware
    # Invalidate signature
    manifest_data["signature"] = "00" * 64

    states = []
    results = []

    worker = FirmwareFlashWorker(
        port="COM99_NONEXISTENT",
        manifest_data=manifest_data,
        hex_path=hex_path,
        current_firmware_version="1.0.0"
    )
    worker.stateChanged.connect(lambda s: states.append(s))
    worker.flashCompleted.connect(lambda success, msg: results.append((success, msg)))

    worker.run()

    assert "FAILED" in states
    assert len(results) == 1
    assert results[0][0] is False
    assert "security rejection" in results[0][1].lower()

def test_flasher_unavailable_port_failure(valid_firmware):
    hex_path, manifest_data = valid_firmware

    states = []
    results = []

    stop_fn = MagicMock()
    resume_fn = MagicMock()

    worker = FirmwareFlashWorker(
        port="COM99_NONEXISTENT_PORT",
        manifest_data=manifest_data,
        hex_path=hex_path,
        current_firmware_version="1.0.0",
        stop_telemetry_fn=stop_fn,
        resume_telemetry_fn=resume_fn
    )
    worker.stateChanged.connect(lambda s: states.append(s))
    worker.flashCompleted.connect(lambda success, msg: results.append((success, msg)))

    worker.run()

    assert "STOPPING_TELEMETRY" in states
    assert "FAILED" in states
    assert stop_fn.called
    assert resume_fn.called  # Ensured resume on failure
    assert len(results) == 1
    assert results[0][0] is False
    assert "unavailable" in results[0][1].lower()

def test_flasher_user_abort_before_flash(valid_firmware):
    hex_path, manifest_data = valid_firmware

    worker = FirmwareFlashWorker(
        port="COM99",
        manifest_data=manifest_data,
        hex_path=hex_path
    )
    worker.abort()
    results = []
    worker.flashCompleted.connect(lambda success, msg: results.append((success, msg)))

    worker.run()

    assert len(results) == 1
    assert results[0][0] is False
    assert "cancelled" in results[0][1].lower()
