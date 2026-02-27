# ============================================================================
# PagePulse — Production Dockerfile
# Multi-stage build | Non-root user | Auto-migrations | Signal handling
# ============================================================================

# ---------- Stage 1: Build ----------
FROM python:3.12-slim AS builder

WORKDIR /build

# Install build-time system dependencies (gcc for bcrypt C extension)
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency manifest first for layer caching
COPY pyproject.toml README.md ./
COPY src/ ./src/

# Install dependencies into an isolated virtual env
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir .

# ---------- Stage 2: Runtime ----------
FROM python:3.12-slim AS runtime

# Security: create non-root user
RUN groupadd --gid 1000 appuser \
    && useradd --uid 1000 --gid 1000 --shell /bin/bash --create-home appuser

WORKDIR /app

# Copy virtual env from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application source, Alembic config, and entrypoint
COPY alembic.ini ./
COPY alembic/ ./alembic/
COPY src/ ./src/
COPY docker-entrypoint.sh ./

# Make entrypoint executable and create data directory
RUN chmod +x docker-entrypoint.sh \
    && mkdir -p /data \
    && chown -R appuser:appuser /data /app

# Environment defaults
ENV APP_ENV="production" \
    DEBUG="false" \
    DATABASE_URL="sqlite+aiosqlite:///data/pagepulse.db" \
    PYTHONUNBUFFERED="1" \
    PYTHONDONTWRITEBYTECODE="1"

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"]

# Switch to non-root user
USER appuser

# Entrypoint runs migrations, then exec's the CMD for proper signal handling
ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--app-dir", "src"]
