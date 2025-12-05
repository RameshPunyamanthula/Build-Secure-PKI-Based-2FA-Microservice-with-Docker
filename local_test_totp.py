# local_test_totp.py
from fastapi.testclient import TestClient
import main
import json, sys

client = TestClient(main.app)

print("== GET /health ==")
r = client.get("/health")
print(r.status_code)
print(r.text)

print("\n== GET /generate-2fa ==")
r = client.get("/generate-2fa")
print(r.status_code)
print(r.text)
try:
    data = r.json()
    code = data.get("code")
    print("Code:", code, "valid_for:", data.get("valid_for"))
except Exception as e:
    print("Parse error:", e)
    sys.exit(1)

print("\n== POST /verify-2fa (using code above) ==")
r2 = client.post("/verify-2fa", json={"code": code})
print(r2.status_code)
print(r2.text)
