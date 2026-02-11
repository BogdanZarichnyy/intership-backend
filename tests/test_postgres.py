import pytest
from sqlalchemy import text
from app.db.postgres import engine

@pytest.mark.asyncio
async def test_postgres_connection():
  async with engine.connect() as conn:
    result = await conn.execute(text("SELECT 1"))
    assert result is not None
