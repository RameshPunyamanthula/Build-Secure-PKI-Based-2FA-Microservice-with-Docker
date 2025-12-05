# crypto_utils.py
import base64
from pathlib import Path
import stat

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend


def load_private_key(path: str, password: bytes = None):
    """
    Load PEM private key from file.
    - path: path to student_private.pem
    - password: None (most likely not password-protected for this assignment)
    Returns: private_key object
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Private key not found: {path}")
    data = p.read_bytes()
    # Remove BOM if present (defensive)
    if data.startswith(b'\xef\xbb\xbf'):
        data = data.lstrip(b'\xef\xbb\xbf')
    private_key = serialization.load_pem_private_key(
        data,
        password=password,
        backend=default_backend()
    )
    return private_key


def decrypt_seed(encrypted_seed_b64: str, private_key) -> str:
    """
    Decrypt base64-encoded encrypted seed using RSA/OAEP (SHA-256 + MGF1(SHA-256)).

    Returns:
        hex_seed (64-character lowercase hex string)

    Raises:
        ValueError on invalid format or decryption failure.
    """
    if not isinstance(encrypted_seed_b64, str) or not encrypted_seed_b64.strip():
        raise ValueError("encrypted_seed_b64 must be a non-empty string")

    # 1) Base64 decode
    try:
        ciphertext = base64.b64decode(encrypted_seed_b64.strip())
    except Exception as e:
        raise ValueError(f"Base64 decode failed: {e}")

    # 2) RSA/OAEP decrypt with SHA-256 & MGF1
    try:
        plaintext_bytes = private_key.decrypt(
            ciphertext,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
    except Exception as e:
        # Do not leak secrets in error; keep message useful for dev
        raise ValueError(f"RSA decryption failed: {e}")

    # 3) Decode to UTF-8 string
    try:
        hex_seed = plaintext_bytes.decode("utf-8").strip()
    except Exception as e:
        raise ValueError(f"Failed to decode plaintext as UTF-8: {e}")

    # 4) Validate: must be 64-character hex using lowercase characters 0-9 a-f
    hex_seed = hex_seed.lower()
    if len(hex_seed) != 64:
        raise ValueError(f"Invalid seed length: expected 64 chars, got {len(hex_seed)}")
    allowed = set("0123456789abcdef")
    if any(c not in allowed for c in hex_seed):
        raise ValueError("Seed contains invalid characters: must be lowercase hex [0-9a-f]")

    return hex_seed


def save_seed_to_data(hex_seed: str, path: str = "/data/seed.txt"):
    """
    Save the hex seed to persistent /data/seed.txt and set secure permissions.
    """
    p = Path(path)
    # ensure parent exists (in container /data will be mounted)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(hex_seed + "\n", encoding="utf-8")
    # set secure permissions (owner read/write only)
    try:
        p.chmod(0o600)
    except Exception:
        # on some systems (Windows) chmod may do nothing; ignore but warn if necessary
        pass
    return str(p)
