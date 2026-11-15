import os
from pathlib import Path
import pytest

TEST_PRIVKEY_HEX = "9d61b19deffd5a60ba844af492ec2cc44449c5697b326919703bac031cae7f60"
TEST_PUBKEY_HEX = "d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a"

def get_test_signing_key():
    from cryptography.hazmat.primitives.asymmetric import ed25519
    key_path = Path("private_keys/devpro_firmware_signing.key")
    if key_path.exists():
        from cryptography.hazmat.primitives.serialization import load_pem_private_key
        return load_pem_private_key(key_path.read_bytes(), password=None)
    else:
        os.environ["DEVPRO_FIRMWARE_PUBKEY_HEX"] = TEST_PUBKEY_HEX
        return ed25519.Ed25519PrivateKey.from_private_bytes(bytes.fromhex(TEST_PRIVKEY_HEX))

@pytest.fixture(autouse=True)
def configure_test_environment():
    key_path = Path("private_keys/devpro_firmware_signing.key")
    if not key_path.exists():
        os.environ["DEVPRO_FIRMWARE_PUBKEY_HEX"] = TEST_PUBKEY_HEX
    yield
