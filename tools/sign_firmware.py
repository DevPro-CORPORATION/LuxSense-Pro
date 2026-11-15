"""
LuxSense Pro — Official Firmware Signing Utility
Signs compiled Arduino ATmega328P firmware images with DevPro-CORP Ed25519 root private key.
Generates cryptographically signed firmware-manifest.json.
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime, timezone
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives.serialization import load_pem_private_key

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from software.core.firmware_security import (
    DEVPRO_FIRMWARE_PUBKEY_HEX,
    FirmwareManifest,
    compute_file_sha256,
    verify_firmware_package
)

def sign_firmware(
    hex_path: Path,
    manifest_out: Path,
    private_key_path: Path,
    version: str = "2.0.0",
    release_name: str = "LuxSense Pro Microcode v2.0.0 (Scientific Radiometry)",
    release_notes: str = "Official v2.0.0 firmware featuring dynamic dual-address I2C detection, handshake verification, and explicit disconnection reporting."
) -> bool:
    if not hex_path.exists():
        print(f"[Signer] Error: Hex file not found at {hex_path}")
        return False

    if not private_key_path.exists():
        print(f"[Signer] Error: Private key file not found at {private_key_path}")
        return False

    # Load Ed25519 private key
    priv_bytes = private_key_path.read_bytes()
    private_key = load_pem_private_key(priv_bytes, password=None)

    hex_sha = compute_file_sha256(hex_path)
    hex_size = hex_path.stat().st_size

    manifest_obj = FirmwareManifest(
        firmware_version=version,
        release_name=release_name,
        published_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        target_board="arduino:avr:uno",
        target_mcu="atmega328p",
        bootloader="optiboot",
        baud_rate=115200,
        clock_mhz=16,
        supported_sensors=["BH1750 (0x23)", "BH1750 (0x5C)"],
        min_app_version="2.0.0",
        hex_filename=hex_path.name,
        hex_sha256=hex_sha,
        hex_size=hex_size,
        release_notes=release_notes,
        publisher="DevPro-CORP Root Authority",
        signature=""
    )

    canonical_data = manifest_obj.canonical_bytes()
    signature_bytes = private_key.sign(canonical_data)
    manifest_obj.signature = signature_bytes.hex()

    manifest_dict = manifest_obj.__dict__
    manifest_out.parent.mkdir(parents=True, exist_ok=True)
    with open(manifest_out, "w", encoding="utf-8") as f:
        json.dump(manifest_dict, f, indent=2)

    print(f"[Signer] Generated signed manifest: {manifest_out}")
    print(f"[Signer] Firmware Version : {version}")
    print(f"[Signer] SHA-256 Digest   : {hex_sha}")
    print(f"[Signer] Ed25519 Signature: {manifest_obj.signature[:32]}...")

    # Self-test verification
    valid, msg, _ = verify_firmware_package(manifest_dict, hex_path=hex_path)
    if valid:
        print(f"[Signer] Self-test verification: PASSED ({msg})")
        return True
    else:
        print(f"[Signer] Self-test verification: FAILED ({msg})")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sign LuxSense Pro Arduino Firmware")
    parser.add_argument("--hex", type=Path, default=ROOT_DIR / "firmware" / "build" / "LuxSense_Arduino.ino.hex")
    parser.add_argument("--out", type=Path, default=ROOT_DIR / "dist_installer" / "firmware-manifest.json")
    parser.add_argument("--key", type=Path, default=ROOT_DIR / "private_keys" / "devpro_firmware_signing.key")
    parser.add_argument("--version", type=str, default="2.0.0")

    args = parser.parse_args()
    success = sign_firmware(args.hex, args.out, args.key, version=args.version)
    sys.exit(0 if success else 1)
