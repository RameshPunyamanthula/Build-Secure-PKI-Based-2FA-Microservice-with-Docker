#!/usr/bin/env python3
# sign_and_encrypt.py
# Usage: python sign_and_encrypt.py
# Requires: student_private.pem and instructor_public.pem in repo root

import base64
import subprocess
from pathlib import Path
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.backends import default_backend

# Helpers
def get_commit_hash():
    # Get latest commit hash from git
    try:
        out = subprocess.check_output(["git", "log", "-1", "--format=%H"], stderr=subprocess.DEVNULL)
        h = out.decode("utf-8").strip()
        if len(h) != 40:
            raise RuntimeError("Unexpected git commit hash length")
        return h
    except Exception as e:
        raise RuntimeError(f"Failed to get commit hash via git: {e}")

def load_private_key(path="student_private.pem"):
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"{path} not found")
    data = p.read_bytes()
    return serialization.load_pem_private_key(data, password=None, backend=default_backend())

def load_public_key(path="instructor_public.pem"):
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"{path} not found")
    data = p.read_bytes()
    return serialization.load_pem_public_key(data, backend=default_backend())

def sign_commit_hash(commit_hash: str, private_key) -> bytes:
    # Sign ASCII commit hash bytes using RSA-PSS with SHA-256 and max salt length
    m = commit_hash.encode("utf-8")
    sig = private_key.sign(
        m,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    return sig

def encrypt_signature(signature: bytes, public_key) -> bytes:
    # Encrypt signature bytes using RSA-OAEP with SHA-256 (MGF1 SHA-256)
    ct = public_key.encrypt(
        signature,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return ct

def main():
    try:
        commit_hash = get_commit_hash()
        print("Commit Hash:", commit_hash)
    except Exception as e:
        print("ERROR:", e)
        return 2

    try:
        priv = load_private_key("student_private.pem")
    except Exception as e:
        print("ERROR loading private key:", e)
        return 3

    try:
        sig = sign_commit_hash(commit_hash, priv)
    except Exception as e:
        print("ERROR signing commit hash:", e)
        return 4

    try:
        instr_pub = load_public_key("instructor_public.pem")
    except Exception as e:
        print("ERROR loading instructor public key:", e)
        return 5

    try:
        enc = encrypt_signature(sig, instr_pub)
    except Exception as e:
        print("ERROR encrypting signature with instructor public key:", e)
        return 6

    b64 = base64.b64encode(enc).decode("utf-8")
    # Save outputs
    Path("commit_hash.txt").write_text(commit_hash + "\n", encoding="utf-8")
    Path("encrypted_signature.txt").write_text(b64 + "\n", encoding="utf-8")
    print("\nEncrypted Signature (base64, single line saved to encrypted_signature.txt):")
    print(b64)
    print("\nSaved files: commit_hash.txt, encrypted_signature.txt")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
