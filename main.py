# main.py
import base64
import time
from pathlib import Path
from typing import Optional

import pyotp
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel

app = FastAPI(title="PKI-2FA Microservice (TOTP Endpoints)")

# CONFIG: where to look for the decrypted hex seed (prefer PWD seed.txt, fallback to /data/seed.txt)
SEED_PATHS = [Path("seed.txt"), Path("/data/seed.txt")]


def _read_hex_seed() -> str:
    """
    Read the 64-char hex seed from disk.
    Looks in PWD seed.txt first, then /data/seed.txt.
    Raises FileNotFoundError if not found.
    """
    for p in SEED_PATHS:
        if p.exists():
            txt = p.read_text(encoding="utf-8").strip()
            if txt:
                return txt.strip()
    raise FileNotFoundError("Seed file not found in expected locations.")


def _hex_to_base32(hex_seed: str) -> str:
    """
    Convert 64-character hex string to base32 string for TOTP.
    """
    # Validate hex length
    hex_seed = hex_seed.strip().lower()
    if len(hex_seed) != 64:
        raise ValueError("Seed must be 64 hex characters.")
    # convert hex -> bytes -> base32 string (no padding removal necessary)
    seed_bytes = bytes.fromhex(hex_seed)
    b32 = base64.b32encode(seed_bytes).decode("utf-8")
    return b32


def generate_totp_code_from_hex(hex_seed: str) -> (str, int):
    """
    Generate TOTP code and return (code_str, valid_for_seconds).
    - SHA-1, 30s period, 6 digits (pyotp default)
    """
    base32_seed = _hex_to_base32(hex_seed)
    totp = pyotp.TOTP(base32_seed, digits=6, interval=30)  # SHA1 default
    code = totp.now()
    # seconds remaining in current 30s period
    epoch = int(time.time())
    valid_for = 30 - (epoch % 30)
    return code, valid_for


def verify_totp_code_from_hex(hex_seed: str, code: str, valid_window: int = 1) -> bool:
    """
    Verify TOTP code with ±valid_window periods tolerance.
    Returns True if valid, False otherwise.
    """
    base32_seed = _hex_to_base32(hex_seed)
    totp = pyotp.TOTP(base32_seed, digits=6, interval=30)
    # pyotp's verify accepts valid_window argument for ±N windows
    try:
        return totp.verify(code, valid_window=valid_window)
    except Exception:
        return False


# Request/response models
class VerifyRequest(BaseModel):
    code: Optional[str]


@app.get("/generate-2fa")
async def generate_2fa():
    """
    Read seed from disk, generate current TOTP code and seconds left.
    Returns: {"code": "123456", "valid_for": 30}
    """
    try:
        hex_seed = _read_hex_seed()
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail={"error": "Seed not decrypted yet"})
    try:
        code, valid_for = generate_totp_code_from_hex(hex_seed)
        return {"code": code, "valid_for": valid_for}
    except ValueError as e:
        raise HTTPException(status_code=500, detail={"error": str(e)})


@app.post("/verify-2fa")
async def verify_2fa(req: VerifyRequest):
    """
    Accepts JSON body: {"code": "123456"}
    Returns: {"valid": true/false}
    """
    if req.code is None:
        # missing code
        raise HTTPException(status_code=400, detail={"error": "Missing code"})
    code = str(req.code).strip()
    if not code:
        raise HTTPException(status_code=400, detail={"error": "Missing code"})

    try:
        hex_seed = _read_hex_seed()
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail={"error": "Seed not decrypted yet"})

    valid = verify_totp_code_from_hex(hex_seed, code, valid_window=1)
    return {"valid": bool(valid)}


@app.get("/health")
async def health():
    return {"status": "ok"}
# --- /decrypt-seed endpoint (appended) ---
from pydantic import BaseModel
from fastapi import HTTPException

# crypto helper functions (must be in crypto_utils.py)
from crypto_utils import load_private_key, decrypt_seed, save_seed_to_data

class DecryptRequest(BaseModel):
    encrypted_seed: str

@app.post("/decrypt-seed")
async def decrypt_seed_endpoint(req: DecryptRequest):
    """
    Accepts JSON: {"encrypted_seed":"BASE64..."}
    Success -> 200 {"status":"ok"}
    400 -> missing encrypted_seed
    500 -> decryption / key load / save failures
    """
    enc = (req.encrypted_seed or "").strip()
    if not enc:
        raise HTTPException(status_code=400, detail={"error": "Missing encrypted_seed"})

    # Load private key
    try:
        private_key = load_private_key("student_private.pem")
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail={"error": "Private key not found"})
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": "Private key load failed"})

    # Decrypt seed
    try:
        hex_seed = decrypt_seed(enc, private_key)
    except Exception:
        raise HTTPException(status_code=500, detail={"error": "Decryption failed"})

    # Save seed persistently. Try container path first, fallback to PWD seed.txt
    try:
        save_seed_to_data(hex_seed, "/data/seed.txt")
    except Exception:
        try:
            save_seed_to_data(hex_seed, "seed.txt")
        except Exception:
            raise HTTPException(status_code=500, detail={"error": "Failed to save seed"})

    return {"status": "ok"}
# --- end appended endpoint ---
