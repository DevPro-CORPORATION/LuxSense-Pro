"""
LuxSense Pro — Encrypted Serial Packet Decryptor
Validates rolling-key XOR packets and checksums from Arduino Uno + BH1750.
"""

from typing import Optional, Tuple
from app.core.config import SECRET_KEY

def decrypt_packet(packet_hex: str) -> Optional[Tuple[int, float]]:
    """
    Decodes rolling-key XOR encrypted sensor telemetry.
    Returns (packet_id, lux) if XOR pattern and checksum validate, else None.
    """
    try:
        raw = bytes.fromhex(packet_hex.strip())
        if not raw:
            return None

        for offset in range(16):
            decoded = bytes(
                value ^ SECRET_KEY[(index + offset) % 16]
                for index, value in enumerate(raw)
            )
            try:
                fields = decoded.decode("ascii").split("|")
            except UnicodeDecodeError:
                continue

            if len(fields) != 3:
                continue

            packet_text, lux_text, checksum_text = fields
            try:
                packet_id = int(packet_text)
                lux = float(lux_text)
                checksum = int(checksum_text)
            except ValueError:
                continue

            if not (0.0 <= lux < 1_000_000 and 0 <= checksum <= 255):
                continue

            packet_id %= 65536
            lux_hundredths = int(lux * 100.0 + 0.5)

            if packet_id % 16 == offset:
                if (packet_id + lux_hundredths) % 256 == checksum:
                    return packet_id, lux

    except Exception:
        pass

    return None
