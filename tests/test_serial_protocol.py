"""
Unit Tests for Rolling-Key XOR Encryption & Checksum Verification
"""

from software.core.crypto_packet import decrypt_packet
from software.core.config import SECRET_KEY

def encrypt_test_packet(packet_id: int, lux: float) -> str:
    lux_hundredths = int(lux * 100.0 + 0.5)
    checksum = (packet_id + lux_hundredths) % 256
    payload = f"{packet_id}|{lux:.2f}|{checksum}".encode("ascii")

    hex_chars = []
    for i, byte_val in enumerate(payload):
        enc = byte_val ^ SECRET_KEY[(i + packet_id) % 16]
        hex_chars.append(f"{enc:02X}")
    return "".join(hex_chars)

def test_encrypted_packet_roundtrip():
    packet_hex = encrypt_test_packet(1, 123.45)
    result = decrypt_packet(packet_hex)
    assert result is not None
    p_id, lux = result
    assert p_id == 1
    assert round(lux, 2) == 123.45

    packet_hex_17 = encrypt_test_packet(17, 5000.50)
    result_17 = decrypt_packet(packet_hex_17)
    assert result_17 is not None
    p_id_17, lux_17 = result_17
    assert p_id_17 == 17
    assert round(lux_17, 2) == 5000.50

def test_corrupted_packet_rejected():
    valid_hex = encrypt_test_packet(42, 850.00)
    corrupted_hex = "FF" + valid_hex[2:]
    result = decrypt_packet(corrupted_hex)
    assert result is None
