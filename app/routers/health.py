import asyncio
from fastapi import APIRouter, status
from pydantic import BaseModel
from sqlalchemy import text
from app.config import settings
from app.db.postgres import engine
from app.db.redis import redis_client

router = APIRouter()

class HealthResponse(BaseModel):
  status: str
  postgres: str
  redis: str
  message: str

async def check_postgres() -> str:
  try:
    async with engine.connect() as conn:
      await asyncio.wait_for(conn.execute(text("SELECT 1")), timeout=settings.retry_delay)
    return "ok"
  except Exception:
    return "error"

async def check_redis() -> str:
  try:
    await asyncio.wait_for(redis_client.ping(), timeout=settings.retry_delay)
    return "ok"
  except Exception:
    return "error"

@router.get(
  "/", 
  response_model=HealthResponse, 
  status_code=status.HTTP_200_OK
)
async def health_check():
  postgres_status, redis_status = await asyncio.gather(
    check_postgres(),
    check_redis()
  )
  overall_status = "ok" if postgres_status == "ok" and redis_status == "ok" else "error"
  return HealthResponse(
    status=overall_status,
    postgres=postgres_status,
    redis=redis_status,
    message="backend working"
  )
