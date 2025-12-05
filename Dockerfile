# Stage 1: Builder
FROM python:3.11-slim AS builder
WORKDIR /build

# Install build tools for Python wheels if needed (kept minimal)
RUN apt-get update && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements first to leverage layer caching
COPY requirements.txt .

# Install dependencies into a custom prefix (we'll copy these into runtime)
RUN python -m pip install --upgrade pip \
    && python -m pip install --prefix=/install -r requirements.txt

# Copy the rest of the source
COPY . .

# Stage 2 (runtime) skeleton begins here
FROM python:3.11-slim AS runtime
ENV TZ=UTC
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app
# ---------------- Runtime stage continued ----------------
# Install system deps and timezone data, then copy installed packages and app
RUN apt-get update && apt-get install -y --no-install-recommends \
    cron tzdata && rm -rf /var/lib/apt/lists/*

# Configure timezone to UTC
RUN ln -fs /usr/share/zoneinfo/UTC /etc/localtime && echo "UTC" > /etc/timezone

# Copy installed Python packages from builder
COPY --from=builder /install /usr/local

# Copy application code into image
COPY --from=builder /build /app

# Ensure cron script is executable
RUN chmod +x /app/scripts/log_2fa_cron.py || true

# Install cron job file (expect cron/2fa-cron in repo)
RUN if [ -f /app/cron/2fa-cron ]; then cp /app/cron/2fa-cron /etc/cron.d/2fa-cron && chmod 0644 /etc/cron.d/2fa-cron && crontab /etc/cron.d/2fa-cron; fi

# Create mount points
RUN mkdir -p /data /cron && chmod 0755 /data /cron

# Expose port 8080
EXPOSE 8080

# Add a small startup script that starts cron (service or cron -f) and uvicorn
RUN printf '%s\n' '#!/bin/sh' 'export TZ=UTC' 'if command -v service >/dev/null 2>&1; then service cron start; else cron -f & fi' 'python -m uvicorn main:app --host 0.0.0.0 --port 8080' > /usr/local/bin/startup.sh
RUN chmod +x /usr/local/bin/startup.sh

CMD ["/usr/local/bin/startup.sh"]
