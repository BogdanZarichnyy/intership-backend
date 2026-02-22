#!/bin/sh

set -e

echo "Waiting for PostgreSQL..."

# простий retry механізм
until alembic upgrade head
do
  echo "Database not ready, retrying in 2 seconds..."
  sleep 2
done

echo "Migrations applied successfully"

echo "Starting application..."

exec python -m app.main
