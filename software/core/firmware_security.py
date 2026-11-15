"""
LuxSense Pro — Firmware Security & Digital Signature Engine
Provides cryptographic verification of Arduino firmware manifests and binary images.
Enforces publisher authentication (Ed25519), SHA-256 hash matching, MCU/board
compatibility, and downgrade prevention.
"""

import os
import sys
import json
import hashlib
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any, Tuple
from packaging.version import parse as parse_version

# DevPro-CORP Root Firmware Authority — Ed25519 Public Key (32 bytes Raw Hex)
# All official LuxSense Pro Arduino firmware releases are signed with the matching private key.
DEVPRO_FIRMWARE_PUBKEY_HEX = "9a1dc8f01459c05ebb77abbfc71f3b36b00f5aafdf1bc186914085d24bb52d0d"

@dataclass
class FirmwareManifest:
    firmware_version: str
    release_name: str
    published_at: str
    target_board: str
    target_mcu: str
    bootloader: str
    baud_rate: int
    clock_mhz: int
    supported_sensors: list
    min_app_version: str
    hex_filename: str
    hex_sha256: str
    hex_size: int
    release_notes: str
    publisher: str
    signature: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FirmwareManifest":
        fields = cls.__dataclass_fields__.keys()
        filtered = {k: data[k] for k in fields if k in data}
        return cls(**filtered)

    def canonical_bytes(self) -> bytes:
        """Return deterministic canonical byte sequence for signing and verification."""
        data = asdict(self)
        data.pop("signature", None)
        return json.dumps(data, sort_keys=True, separators=(',', ':')).encode('utf-8')


def compute_file_sha256(filepath: Path) -> str:
    """Compute SHA-256 hash of a local file."""
    sha = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            sha.update(chunk)
    return sha.hexdigest().lower()


def verify_ed25519_signature(message: bytes, signature_hex: str, public_key_hex: str = DEVPRO_FIRMWARE_PUBKEY_HEX) -> Tuple[bool, str]:
    """Verify an Ed25519 digital signature against a public key."""
    try:
        from cryptography.hazmat.primitives.asymmetric import ed25519
        from cryptography.exceptions import InvalidSignature

        pub_bytes = bytes.fromhex(public_key_hex)
        sig_bytes = bytes.fromhex(signature_hex)

        public_key = ed25519.Ed25519PublicKey.from_public_bytes(pub_bytes)
        public_key.verify(sig_bytes, message)
        return True, "Valid DevPro-CORP Ed25519 Publisher Signature"
    except ImportError:
        # If cryptography is not available, fail-safe to verification error
        return False, "Cryptographic verification library (cryptography) is not installed."
    except InvalidSignature:
        return False, "Digital signature verification failed: signature does not match manifest payload."
    except Exception as e:
        return False, f"Signature verification error: {str(e)}"


def verify_firmware_package(
    manifest_data: Dict[str, Any],
    hex_path: Optional[Path] = None,
    current_firmware_version: Optional[str] = None,
    allow_downgrade: bool = False,
    expected_board: str = "arduino:avr:uno",
    expected_mcu: str = "atmega328p"
) -> Tuple[bool, str, Optional[FirmwareManifest]]:
    """
    Complete security evaluation of a firmware package:
    1. Validates required manifest fields.
    2. Cryptographically verifies Ed25519 publisher signature.
    3. Verifies board and MCU architecture compatibility.
    4. Evaluates downgrade rules.
    5. Verifies binary image SHA-256 integrity and byte length (if hex_path provided).
    """
    try:
        manifest = FirmwareManifest.from_dict(manifest_data)
    except Exception as e:
        return False, f"Malformed firmware manifest: {str(e)}", None

    if not manifest.signature:
        return False, "Security violation: Firmware manifest is unsigned.", None

    # Step 1: Verify digital signature
    canonical_payload = manifest.canonical_bytes()
    sig_ok, sig_msg = verify_ed25519_signature(canonical_payload, manifest.signature)
    if not sig_ok:
        return False, f"Security rejection: {sig_msg}", manifest

    # Step 2: Architecture & MCU Compatibility check
    def normalize_board(b: str) -> str:
        b_clean = b.lower().strip()
        if "uno" in b_clean:
            return "uno"
        if "nano" in b_clean:
            return "nano"
        return b_clean

    board_norm = normalize_board(manifest.target_board)
    expected_norm = normalize_board(expected_board)
    compatible_family = {"uno", "nano"}

    if board_norm != expected_norm and not (board_norm in compatible_family and expected_norm in compatible_family):
        return False, (
            f"Hardware incompatibility: Firmware targets '{manifest.target_board}', "
            f"but connected hardware requires '{expected_board}'."
        ), manifest

    if manifest.target_mcu.lower() != expected_mcu.lower():
        return False, (
            f"MCU incompatibility: Firmware compiled for '{manifest.target_mcu}', "
            f"but connected board is '{expected_mcu}'."
        ), manifest

    # Step 3: Downgrade Evaluation
    if current_firmware_version and not allow_downgrade:
        try:
            curr_v = parse_version(current_firmware_version)
            cand_v = parse_version(manifest.firmware_version)
            if cand_v < curr_v:
                return False, (
                    f"Downgrade prohibited: Target version v{manifest.firmware_version} "
                    f"is older than currently installed v{current_firmware_version}. "
                    f"Explicit authorization is required."
                ), manifest
        except Exception:
            pass

    # Step 4: Verify binary integrity if hex path supplied
    if hex_path is not None:
        if not hex_path.exists():
            return False, f"Firmware hex image not found: {hex_path}", manifest

        computed_sha = compute_file_sha256(hex_path)
        if computed_sha.lower() != manifest.hex_sha256.lower():
            return False, (
                f"Binary integrity violation: SHA-256 mismatch!\n"
                f"Expected: {manifest.hex_sha256}\n"
                f"Computed: {computed_sha}\n"
                f"Firmware file may be corrupted or modified."
            ), manifest

        actual_size = hex_path.stat().st_size
        if manifest.hex_size > 0 and actual_size != manifest.hex_size:
            return False, (
                f"Binary integrity violation: Size mismatch! "
                f"Expected {manifest.hex_size} bytes, got {actual_size} bytes."
            ), manifest

    return True, "Firmware package cryptographically verified and approved for flashing.", manifest
