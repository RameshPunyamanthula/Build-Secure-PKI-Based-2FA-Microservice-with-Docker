Build Secure PKI-Based 2FA Microservice with Docker

This project implements a fully secure Public Key Infrastructure (PKI) based Two-Factor Authentication (2FA) microservice, built as part of the GPP TAK2 assignment.
It uses RSA cryptography, TOTP generation, Docker, and a cron-based logging system to create a production-ready authentication module.

📌 Project Overview
1️⃣ Seed Decryption (RSA-OAEP-SHA256)

The instructor provides an encrypted seed, which is decrypted using the student's private RSA-4096 key inside the container.
The decrypted seed is stored at:

/data/seed.txt

2️⃣ TOTP Generation (SHA-1 / 30 seconds / 6 digits)

Using the decrypted seed, the microservice generates a 6-digit TOTP code, compatible with authenticator apps.

🧩 API Endpoints (FastAPI)
POST /decrypt-seed

Decrypts the encrypted seed and saves it.

GET /generate-2fa

Generates the current TOTP and remaining validity time.

POST /verify-2fa

Verifies a submitted TOTP code.

GET /health

Simple health check.

🕒 Cron Job (Inside Docker)

A cron job runs every minute and logs the current TOTP code:

YYYY-MM-DD HH:MM:SS - 2FA Code: XXXXXX


Stored in:

/cron/last_code.txt

🗂 Project Structure
├── main.py
├── crypto_utils.py
├── generate_keys.py
├── request_seed.py
├── do_decrypt.py
├── sign_and_encrypt.py
├── Dockerfile
├── docker-compose.yml
├── cron/2fa-cron
├── scripts/log_2fa_cron.py
├── student_private.pem
├── student_public.pem
├── instructor_public.pem
├── requirements.txt
└── encrypted_seed.txt (ignored)

🚀 How to Run Locally
1️⃣ Build Docker image
docker-compose build --no-cache

2️⃣ Start container
docker-compose up -d

3️⃣ Test API

Health

curl http://localhost:8080/health


Decrypt Seed

curl -X POST http://localhost:8080/decrypt-seed \
-H "Content-Type: application/json" \
-d "{\"encrypted_seed\": \"$(cat encrypted_seed.txt)\"}"


Generate TOTP

curl http://localhost:8080/generate-2fa


Verify TOTP

curl -X POST http://localhost:8080/verify-2fa \
-H "Content-Type: application/json" \
-d "{\"code\": \"123456\"}"

📁 Cron Logging Verification

Wait 60 seconds, then:

docker exec pki_2fa_app cat /cron/last_code.txt

🔐 Security Features Implemented

RSA-4096 key pair

RSA-OAEP-SHA256 seed decryption

RSA-PSS-SHA256 commit signing

Cron-based secure logging

Docker multi-stage build

Seed persistence using volumes

Error-safe API endpoints

UTC timezone handling

🏗 Production-Ready Improvements

Use Secrets Manager / Vault for private keys

Add TLS / HTTPS

Add API rate limiting

Add Prometheus metrics & logging

Kubernetes auto-scaling & HA

Automated key rotation

CI/CD pipeline
