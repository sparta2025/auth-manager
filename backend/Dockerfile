# ── Stage 1: Dependencies ─────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build

# Устанавливаем только build-зависимости
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Stage 2: Runtime ──────────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

LABEL maintainer="auth-manager"
LABEL version="3.0.0"
LABEL description="Auth Manager Backend — FastAPI + SQLAlchemy + PostgreSQL"

WORKDIR /app

# Runtime system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 curl && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY . .

# Non-root user для безопасности (OWASP: Принцип наименьших привилегий)
RUN useradd --system --no-create-home --shell /bin/false appuser && \
    mkdir -p /app/uploads/avatars && \
    chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=15s --timeout=5s --retries=5 --start-period=30s \
    CMD curl -sf http://localhost:8000/health || exit 1

ENTRYPOINT ["./entrypoint.sh"]
