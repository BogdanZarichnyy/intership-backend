#!/bin/sh

set -e

echo "Waiting for PostgreSQL..."

until python -c "
import asyncio
from app.db.postgres import engine

async def check():
  async with engine.begin() as conn:
    await conn.run_sync(lambda conn: None)

asyncio.run(check())
"
do
  echo "PostgreSQL not ready, retrying..."
  sleep 2
done

echo "PostgreSQL is ready"

echo "Running migrations..."

alembic upgrade head

echo "Starting application..."

exec python -m app.main
