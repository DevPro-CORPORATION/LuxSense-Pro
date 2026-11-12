"""
Unit Tests for Cryptographic Security & Authenticode Verification
"""

import tempfile
from pathlib import Path
from app.updater.security import compute_sha256, verify_sha256, verify_authenticode

def test_compute_and_verify_sha256():
    with tempfile.NamedTemporaryFile("wb", delete=False) as f:
        f.write(b"LuxSense Pro Secure Telemetry Test Payload")
        temp_path = Path(f.name)

    try:
        # Expected SHA-256 for "LuxSense Pro Secure Telemetry Test Payload"
        # Can compute dynamically and verify match
        h = compute_sha256(temp_path)
        assert len(h) == 64
        assert verify_sha256(temp_path, h)
        assert verify_sha256(temp_path, h.upper())

        # Tampered content should fail verification
        tampered_hash = "0" * 64
        assert not verify_sha256(temp_path, tampered_hash)
    finally:
        temp_path.unlink(missing_ok=True)

def test_verify_authenticode_handling():
    # Test file that does not exist
    non_existent = Path("non_existent_binary.exe")
    valid, msg = verify_authenticode(non_existent)
    assert not valid
    assert "does not exist" in msg
