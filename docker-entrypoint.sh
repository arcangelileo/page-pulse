#!/bin/bash
set -e

echo "PagePulse — starting up..."

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

echo "Migrations complete. Starting application..."

# Execute the CMD (uvicorn)
exec "$@"
