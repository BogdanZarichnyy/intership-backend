from contextlib import asynccontextmanager
from fastapi import FastAPI
import asyncio
import uvicorn

from app.core.logger import logger

from app.routers.health import router as healthRouter
from app.routers.user import router as userRouter
from app.core.middleware import setup_middlewares
from app.config import settings

from app.db.postgres import engine
from app.db.redis import redis_client

# --- Параметри повторних спроб ---
MAX_RETRIES = 5
RETRY_DELAY = 2  # секунди

async def wait_for_postgres():
  retries = 0
  while retries < MAX_RETRIES:
    try:
      async with engine.begin() as conn:
        await conn.run_sync(lambda conn: None)
      logger.info("PostgreSQL connected")
      return
    except Exception as e:
      retries += 1
      logger.warning(f"PostgreSQL not ready, retry {retries}/{MAX_RETRIES}: {e}")
      await asyncio.sleep(RETRY_DELAY)
  logger.error("Cannot connect to PostgreSQL")
  raise RuntimeError("Cannot connect to PostgreSQL")

async def wait_for_redis():
  retries = 0
  while retries < MAX_RETRIES:
    try:
      await redis_client.ping()
      logger.info("Redis connected")
      return
    except Exception as e:
      retries += 1
      logger.warning(f"Redis not ready, retry {retries}/{MAX_RETRIES}: {e}")
      await asyncio.sleep(RETRY_DELAY)
  logger.error("Cannot connect to Redis")
  raise RuntimeError("Cannot connect to Redis")

@asynccontextmanager
async def lifespan(app: FastAPI):
  # startup
  await wait_for_postgres()
  await wait_for_redis()
  yield

  # shutdown
  await engine.dispose()
  await redis_client.close()
  logger.info("PostgreSQL disconnected")
  logger.info("Redis disconnected")

def create_app() -> FastAPI: # Використовуємо factory pattern, щоб було легше тестувати
  app = FastAPI(title="Internship Backend", lifespan=lifespan)

  setup_middlewares(app)
  app.include_router(healthRouter)
  app.include_router(userRouter, prefix="/users")

  return app

app = create_app()

if __name__ == "__main__":
  uvicorn.run(
    "app.main:app",
    host=settings.host,
    port=settings.port,
    reload=True
  )
