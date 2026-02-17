from contextlib import asynccontextmanager
from fastapi import FastAPI
import asyncio
import uvicorn

import logging
from logging.handlers import RotatingFileHandler
import os

from alembic import command
from alembic.config import Config

from app.routers.health import router as healthRouter
from app.routers.auth import router as authRouter
from app.routers.user import router as userRouter
from app.core.middleware import setup_middlewares
from app.config import settings

from app.db.postgres import engine
from app.db.redis import redis_client

# --- Логування ---
os.makedirs("logs", exist_ok=True)

logger = logging.getLogger("app")
logger.setLevel(logging.INFO)

formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

# Консоль
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Файл з ротацією
file_handler = RotatingFileHandler("logs/app.log", maxBytes=5_000_000, backupCount=5)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

logger.info("Logger initialized")

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

# --- Автоматичне застосування міграцій ---
async def run_migrations():
  loop = asyncio.get_event_loop()
  alembic_cfg = Config("alembic.ini")

  # Виконуємо синхронний виклик у окремому потоці
  await loop.run_in_executor(None, lambda: command.upgrade(alembic_cfg, "head"))
  logger.info("Database migrations applied successfully")

@asynccontextmanager
async def lifespan(app: FastAPI):
  # startup
  await wait_for_postgres()
  await wait_for_redis()
  await run_migrations()
  yield

  # shutdown
  await engine.dispose()
  await redis_client.close()
  logger.info("PostgreSQL disconnected")
  logger.info("Redis disconnected")

def create_app() -> FastAPI: # Використовуємо factory pattern, щоб було легше тестувати
  app = FastAPI(title="Internship Backend", lifespan=lifespan)

  setup_middlewares(app)

  # Роутери
  app.include_router(healthRouter)
  app.include_router(authRouter, prefix="/auth")
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
