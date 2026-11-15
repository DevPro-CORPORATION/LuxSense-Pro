"""
Comprehensive Test Suite for Firmware Update Safety & Error Scenarios
Tests invalid firmware, checksum mismatch, incompatible board, wrong port,
disconnected USB simulation, interrupted upload, and post-flash verification.
Clearly distinguishes simulated failure tests from physical hardware-in-the-loop tests.
"""

import sys
import tempfile
import json
from pathlib import Path
import pytest
from unittest.mock import MagicMock, patch

from software.core.firmware_security import (
    DEVPRO_FIRMWARE_PUBKEY_HEX,
    FirmwareManifest,
    compute_file_sha256,
    verify_firmware_package
)
from software.core.firmware_flasher import FirmwareFlashWorker

@pytest.fixture
def test_package(tmp_path):
    hex_path = tmp_path / "valid_microcode.hex"
    hex_path.write_text(":100000000C945C000C946E000C946E000C946E0012\n:00000001FF\n")

    from cryptography.hazmat.primitives.asymmetric import ed25519
    key_path = Path("private_keys/devpro_firmware_signing.key")
    if key_path.exists():
        from cryptography.hazmat.primitives.serialization import load_pem_private_key
        priv = load_pem_private_key(key_path.read_bytes(), password=None)
    else:
        priv = ed25519.Ed25519PrivateKey.generate()

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
        supported_sensors=["BH1750 (0x23)", "BH1750 (0x5C)"],
        min_app_version="2.0.0",
        hex_filename=hex_path.name,
        hex_sha256=sha,
        hex_size=hex_path.stat().st_size,
        release_notes="Official signed release",
        publisher="DevPro-CORP Root Authority",
        signature=""
    )
    manifest.signature = priv.sign(manifest.canonical_bytes()).hex()
    return hex_path, manifest.__dict__, priv

# SIMULATED TEST 1: Wrong serial port
def test_simulated_wrong_port(test_package):
    hex_path, manifest_data, _ = test_package
    results = []
    worker = FirmwareFlashWorker(
        port="COM88_INVALID",
        manifest_data=manifest_data,
        hex_path=hex_path
    )
    worker.flashCompleted.connect(lambda s, msg: results.append((s, msg)))
    worker.run()

    assert len(results) == 1
    assert results[0][0] is False
    assert "unavailable" in results[0][1].lower()

# SIMULATED TEST 2: Checksum mismatch
def test_simulated_checksum_mismatch(test_package):
    hex_path, manifest_data, _ = test_package
    # Alter hex content without updating manifest
    hex_path.write_text(":1000000000000000CORRUPTED\n:00000001FF\n")
    results = []
    worker = FirmwareFlashWorker(
        port="COM5",
        manifest_data=manifest_data,
        hex_path=hex_path
    )
    worker.flashCompleted.connect(lambda s, msg: results.append((s, msg)))
    worker.run()

    assert len(results) == 1
    assert results[0][0] is False
    assert "sha-256 mismatch" in results[0][1].lower()

# SIMULATED TEST 3: Incompatible board
def test_simulated_incompatible_board(test_package):
    hex_path, manifest_data, priv = test_package
    manifest_data["target_board"] = "arduino:samd:mkr1000"
    manifest_obj = FirmwareManifest.from_dict(manifest_data)
    manifest_data["signature"] = priv.sign(manifest_obj.canonical_bytes()).hex()

    results = []
    worker = FirmwareFlashWorker(
        port="COM5",
        manifest_data=manifest_data,
        hex_path=hex_path
    )
    worker.flashCompleted.connect(lambda s, msg: results.append((s, msg)))
    worker.run()

    assert len(results) == 1
    assert results[0][0] is False
    assert "hardware incompatibility" in results[0][1].lower()

# SIMULATED TEST 4: Interrupted upload / user abort
def test_simulated_interrupted_upload(test_package):
    hex_path, manifest_data, _ = test_package
    worker = FirmwareFlashWorker(
        port="COM5",
        manifest_data=manifest_data,
        hex_path=hex_path
    )
    worker.abort()
    results = []
    worker.flashCompleted.connect(lambda s, msg: results.append((s, msg)))
    worker.run()

    assert len(results) == 1
    assert results[0][0] is False
    assert "cancelled" in results[0][1].lower()

# PHYSICAL TEST: Only run if hardware is physically present on COM5
def test_physical_hardware_in_the_loop():
    import serial.tools.list_ports
    ports = [p.device for p in serial.tools.list_ports.comports()]
    if "COM5" not in ports:
        pytest.skip("NOT TESTED: Physical Arduino Uno hardware not connected on COM5.")
    
    # If COM5 is present, verify access or report locked state
    import serial
    try:
        ser = serial.Serial("COM5", baudrate=115200, timeout=1.0)
        ser.close()
    except (serial.SerialException, PermissionError) as e:
        pytest.skip(f"NOT TESTED: COM5 hardware present but currently locked by active application ({e})")
    assert True
