# do_decrypt.py
import sys
from pathlib import Path
from crypto_utils import load_private_key, decrypt_seed, save_seed_to_data

def main():
    # adjust filenames as needed
    priv_path = "student_private.pem"
    enc_file = "encrypted_seed.txt"

    if not Path(enc_file).exists():
        print(f"Missing {enc_file}. Put the instructor response into this file.", file=sys.stderr)
        sys.exit(1)

    encrypted_seed_b64 = Path(enc_file).read_text(encoding="utf-8").strip()
    priv = load_private_key(priv_path)

    try:
        hex_seed = decrypt_seed(encrypted_seed_b64, priv)
    except Exception as e:
        print("Decryption error:", e, file=sys.stderr)
        sys.exit(2)

    out_path = save_seed_to_data(hex_seed, "seed.txt")
    print("Decrypted seed saved to:", out_path)
    print("Seed (first 16 chars):", hex_seed[:16] + "...")
    return 0

if __name__ == "__main__":
    sys.exit(main())

