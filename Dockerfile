FROM python:3.12-slim AS base

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files first for layer caching
COPY pyproject.toml README.md ./

# Install Python dependencies
RUN pip install --no-cache-dir .

# Copy application source
COPY alembic.ini ./
COPY alembic/ ./alembic/
COPY src/ ./src/

# Create data directory for SQLite
RUN mkdir -p /data

ENV DATABASE_URL="sqlite+aiosqlite:///data/pagepulse.db"
ENV APP_ENV="production"
ENV DEBUG="false"

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
