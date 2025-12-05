from fastapi.testclient import TestClient
import main
import json, sys, traceback, pathlib

# Load encrypted seed from file
enc_path = pathlib.Path("encrypted_seed.txt")
if not enc_path.exists():
    print("ERROR: encrypted_seed.txt not found")
    sys.exit(2)

enc = enc_path.read_text(encoding="utf-8").strip()

# Initialize TestClient for in-process testing
client = TestClient(main.app)

print("=== Calling /decrypt-seed ===")
try:
    resp = client.post("/decrypt-seed", json={"encrypted_seed": enc})
    print("STATUS_CODE:", resp.status_code)

    # Try to print JSON body nicely
    try:
        print("BODY:", json.dumps(resp.json(), indent=2))
    except Exception:
        print("RAW BODY:", resp.text)

except Exception:
    traceback.print_exc()
    sys.exit(1)
