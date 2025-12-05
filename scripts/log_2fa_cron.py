#!/usr/bin/env python3
# scripts/log_2fa_cron.py
import base64
import time
from pathlib import Path
import datetime
import pyotp

SEED_PATHS = [Path("/data/seed.txt"), Path("seed.txt")]

def read_hex_seed() -> str:
    for p in SEED_PATHS:
        if p.exists():
            txt = p.read_text(encoding="utf-8").strip()
            if txt:
                return txt
    return None

def hex_to_base32(hex_seed: str) -> str:
    hex_seed = hex_seed.strip().lower()
    seed_bytes = bytes.fromhex(hex_seed)
    return base64.b32encode(seed_bytes).decode("utf-8")

def get_totp(hex_seed: str) -> str:
    b32 = hex_to_base32(hex_seed)
    totp = pyotp.TOTP(b32, digits=6, interval=30)
    return totp.now()

def main():
    try:
        seed = read_hex_seed()
        if not seed:
            print("ERROR: seed not found", flush=True)
            return 1
        code = get_totp(seed)
        ts = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        line = f"{ts} - 2FA Code: {code}"
        out = Path("/cron/last_code.txt")
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
        print(line, flush=True)
        return 0
    except Exception as e:
        print("ERROR:", e, flush=True)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
