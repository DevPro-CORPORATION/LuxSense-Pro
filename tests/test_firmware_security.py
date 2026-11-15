"""
Unit Tests for LuxSense Pro Firmware Security & Digital Signatures
Tests Ed25519 publisher signature verification, SHA-256 integrity, MCU compatibility,
downgrade protection, and rejection of tampered packages.
"""

import tempfile
import json
from pathlib import Path
import pytest

from software.core.firmware_security import (
    DEVPRO_FIRMWARE_PUBKEY_HEX,
    FirmwareManifest,
    compute_file_sha256,
    verify_ed25519_signature,
    verify_firmware_package
)

@pytest.fixture
def sample_firmware_hex(tmp_path):
    hex_file = tmp_path / "LuxSense_Arduino.ino.hex"
    # Intel HEX sample
    content = (
        ":100000000C945C000C946E000C946E000C946E0012\n"
        ":100010000C946E000C946E000C946E000C946E0002\n"
        ":00000001FF\n"
    )
    hex_file.write_text(content, encoding="utf-8")
    return hex_file

@pytest.fixture
def signed_manifest_and_key(sample_firmware_hex, tmp_path):
    from tests.conftest import get_test_signing_key
    priv = get_test_signing_key()
    sha = compute_file_sha256(sample_firmware_hex)
    size = sample_firmware_hex.stat().st_size

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
        hex_filename=sample_firmware_hex.name,
        hex_sha256=sha,
        hex_size=size,
        release_notes="Official release test",
        publisher="DevPro-CORP Root Authority",
        signature=""
    )

    canonical_bytes = manifest.canonical_bytes()
    sig = priv.sign(canonical_bytes).hex()
    manifest.signature = sig

    return manifest, priv

def test_valid_firmware_verification(sample_firmware_hex, signed_manifest_and_key):
    manifest, _ = signed_manifest_and_key
    ok, msg, parsed = verify_firmware_package(
        manifest.__dict__,
        hex_path=sample_firmware_hex,
        current_firmware_version="1.2.0"
    )
    assert ok is True
    assert "verified" in msg.lower()
    assert parsed.firmware_version == "2.0.0"

def test_tampered_manifest_rejected(sample_firmware_hex, signed_manifest_and_key):
    manifest, _ = signed_manifest_and_key
    tampered_dict = dict(manifest.__dict__)
    # Attacker alters target version or baud rate
    tampered_dict["baud_rate"] = 57600

    ok, msg, _ = verify_firmware_package(
        tampered_dict,
        hex_path=sample_firmware_hex
    )
    assert ok is False
    assert "signature verification failed" in msg.lower() or "security rejection" in msg.lower()

def test_corrupted_hex_rejected(sample_firmware_hex, signed_manifest_and_key):
    manifest, _ = signed_manifest_and_key
    # Tamper with the hex file content
    sample_firmware_hex.write_text(":100000000C940000TAMPERED\n:00000001FF\n")

    ok, msg, _ = verify_firmware_package(
        manifest.__dict__,
        hex_path=sample_firmware_hex
    )
    assert ok is False
    assert "sha-256 mismatch" in msg.lower()

def test_downgrade_prevention(sample_firmware_hex, signed_manifest_and_key):
    manifest, priv = signed_manifest_and_key
    # Resign manifest with older version 1.1.0
    manifest.firmware_version = "1.1.0"
    manifest.signature = priv.sign(manifest.canonical_bytes()).hex()

    # Attempt to install on a system with 2.0.0 installed
    ok, msg, _ = verify_firmware_package(
        manifest.__dict__,
        hex_path=sample_firmware_hex,
        current_firmware_version="2.0.0",
        allow_downgrade=False
    )
    assert ok is False
    assert "downgrade prohibited" in msg.lower()

    # With explicit authorization, downgrade is allowed
    ok_override, msg_override, _ = verify_firmware_package(
        manifest.__dict__,
        hex_path=sample_firmware_hex,
        current_firmware_version="2.0.0",
        allow_downgrade=True
    )
    assert ok_override is True

def test_incompatible_board_rejected(sample_firmware_hex, signed_manifest_and_key):
    manifest, priv = signed_manifest_and_key
    manifest.target_board = "arduino:esp32:esp32"
    manifest.signature = priv.sign(manifest.canonical_bytes()).hex()

    ok, msg, _ = verify_firmware_package(
        manifest.__dict__,
        hex_path=sample_firmware_hex,
        expected_board="arduino:avr:uno"
    )
    assert ok is False
    assert "hardware incompatibility" in msg.lower()

def test_unsigned_manifest_rejected(sample_firmware_hex, signed_manifest_and_key):
    manifest, _ = signed_manifest_and_key
    data = dict(manifest.__dict__)
    data["signature"] = ""

    ok, msg, _ = verify_firmware_package(data, hex_path=sample_firmware_hex)
    assert ok is False
    assert "unsigned" in msg.lower()

def test_nano_board_compatibility_allowed(sample_firmware_hex, signed_manifest_and_key):
    manifest, priv = signed_manifest_and_key
    manifest.target_board = "arduino:avr:uno"
    manifest.signature = priv.sign(manifest.canonical_bytes()).hex()

    ok, msg, _ = verify_firmware_package(
        manifest.__dict__,
        hex_path=sample_firmware_hex,
        expected_board="arduino:avr:nano"
    )
    assert ok is True
