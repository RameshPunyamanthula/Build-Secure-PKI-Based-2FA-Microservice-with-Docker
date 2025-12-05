
import sys, json
from pathlib import Path
import requests

STUDENT_ID = "23P31A4263"
GITHUB_REPO = "https://github.com/RameshPunyamanthula/Build-Secure-PKI-Based-2FA-Microservice-with-Docker.git"
API_URL = "https://eajeyq4r3zljoq4rpovy2nthda0vtjqf.lambda-url.ap-south-1.on.aws"

def load_and_sanitize_pem(path: Path) -> str:
    txt = path.read_text(encoding="utf-8")
    # Remove BOM if present
    if txt.startswith("\ufeff"):
        txt = txt.lstrip("\ufeff")
    # Strip leading/trailing whitespace
    txt = txt.strip()
    # If the first character is a backslash, remove all leading backslashes (defensive)
    while txt.startswith("\\"):
        txt = txt[1:]
    # Ensure it starts with BEGIN marker
    if not txt.startswith("-----BEGIN PUBLIC KEY-----"):
        print("ERROR: The public key does not start with -----BEGIN PUBLIC KEY-----", file=sys.stderr)
        print("First 80 chars of file:", repr(txt[:80]), file=sys.stderr)
        sys.exit(2)
    return txt  # keep real newlines

def main():
    p = Path("student_public.pem")
    if not p.exists():
        print("ERROR: student_public.pem not found", file=sys.stderr); sys.exit(1)

    pem = load_and_sanitize_pem(p)

    payload = {
        "student_id": STUDENT_ID,
        "github_repo_url": GITHUB_REPO,
        "public_key": pem  # send raw PEM; requests will serialize newlines correctly
    }

    # show a short preview so you can confirm there's no leading backslash
    print("Payload preview (first 200 chars):")
    preview = json.dumps(payload)[:200]
    print(preview)
    print("--- end preview ---\nSending request...")

    try:
        resp = requests.post(API_URL, json=payload, timeout=30)
    except Exception as e:
        print("Network error:", e, file=sys.stderr); sys.exit(3)

    # print full response for debugging
    print("HTTP status:", resp.status_code)
    print("Response body:", resp.text)

    try:
        data = resp.json()
    except Exception:
        print("Failed to parse JSON response. Raw body above.", file=sys.stderr); sys.exit(4)

    if data.get("status") != "success":
        print("API returned error:", json.dumps(data, indent=2), file=sys.stderr); sys.exit(5)

    enc = data.get("encrypted_seed")
    if not enc:
        print("No encrypted_seed in response:", json.dumps(data, indent=2), file=sys.stderr); sys.exit(6)

    Path("encrypted_seed.txt").write_text(enc.strip(), encoding="utf-8")
    print("Saved encrypted_seed.txt (DO NOT commit this file).")
    print("Encrypted seed (first 80 chars):", enc.strip()[:80] + "...")
    return 0

if __name__ == "__main__":
    sys.exit(main())
