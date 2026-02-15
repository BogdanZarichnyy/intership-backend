import pytest
from app.db.redis import redis_client

@pytest.mark.asyncio
async def test_redis_connection():
  pong = await redis_client.ping()
  assert pong is True
