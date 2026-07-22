# ── Stage 1: dependency builder ───────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements-lock.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements-lock.txt


# ── Stage 2: runtime image ────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

LABEL org.opencontainers.image.title="PMAS"
LABEL org.opencontainers.image.description="Project Management Assistant System"
LABEL org.opencontainers.image.version="2.1.0"

# Non-root user for security
RUN groupadd -r pmas && useradd -r -g pmas -d /app -s /sbin/nologin pmas

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application source
COPY backend/ ./backend/
COPY frontend/ ./frontend/
COPY run.py ./

# Data directory — database is stored here and must be mounted as a volume
RUN mkdir -p /data && chown pmas:pmas /data

USER pmas

# Configuration via environment variables
ENV PMAS_DB_PATH=/data/pmas.db \
    PMAS_PORT=8765 \
    PMAS_LOG_LEVEL=INFO \
    PMAS_WORKERS=2

EXPOSE 8765

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:${PMAS_PORT}/health')"

CMD ["sh", "-c", "uvicorn backend.app.main:app --host 0.0.0.0 --port ${PMAS_PORT} --workers ${PMAS_WORKERS}"]
