import pytest
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres"

engine = create_async_engine(DATABASE_URL)

@pytest.mark.asyncio
async def test_postgres_connection():
  async with engine.connect() as conn:
    result = await conn.execute(text("SELECT 1"))
    assert result.scalar() == 1
