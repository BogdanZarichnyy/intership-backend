import pytest
import redis.asyncio as redis

@pytest.mark.asyncio
async def test_redis_connection():
  client = redis.Redis(host="localhost", port=6379)
  try:
    pong = await client.ping()
    assert pong is True
  finally:
    await client.aclose()
