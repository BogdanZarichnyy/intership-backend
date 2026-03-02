from contextlib import asynccontextmanager
from fastapi import FastAPI
import asyncio
import uvicorn

from app.core.logger import logger

from app.routers.health import router as healthRouter
from app.routers.auth import router as authRouter
from app.routers.user import router as userRouter
from app.routers.company import router as companyRouter
from app.routers.company_member import router as companyMemberRouter
from app.routers.company_invitation import router as companyInvitationRouter

from app.middleware.cors import setup_middlewares
from app.middleware.logger_middleware import RequestLoggingMiddleware
from app.middleware.exception_handler import (
  http_exception_handler,
  validation_exception_handler,
  business_error_handler
)
from app.core.exceptions import BusinessError
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import settings

from app.db.postgres import engine
from app.db.redis import redis_client

def setup_exception_handlers(app: FastAPI):
  app.add_exception_handler(StarletteHTTPException, http_exception_handler)
  app.add_exception_handler(RequestValidationError, validation_exception_handler)
  app.add_exception_handler(BusinessError, business_error_handler)

async def wait_for_postgres():
  retries = 0
  while retries < settings.max_retries:
    try:
      async with engine.begin() as conn:
        await conn.run_sync(lambda conn: None)
      logger.info("PostgreSQL connected")
      return
    except Exception as e:
      retries += 1
      logger.warning(f"PostgreSQL not ready, retry {retries}/{settings.max_retries}: {e}")
      await asyncio.sleep(settings.retry_delay)
  logger.error("Cannot connect to PostgreSQL")
  raise RuntimeError("Cannot connect to PostgreSQL")

async def wait_for_redis():
  retries = 0
  while retries < settings.max_retries:
    try:
      await redis_client.ping()
      logger.info("Redis connected")
      return
    except Exception as e:
      retries += 1
      logger.warning(f"Redis not ready, retry {retries}/{settings.max_retries}: {e}")
      await asyncio.sleep(settings.retry_delay)
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
  setup_exception_handlers(app)  # <- підключаємо глобальні хендлери
  app.add_middleware(RequestLoggingMiddleware) # <- підключаємо middleware для логування запитів

  # Роутери
  app.include_router(healthRouter)
  app.include_router(authRouter, prefix="/auth")
  app.include_router(userRouter, prefix="/users")
  app.include_router(companyRouter, prefix="/companies")
  app.include_router(companyMemberRouter, prefix="/company-members")
  app.include_router(companyInvitationRouter, prefix="/company-invitations")

  return app

app = create_app()

if __name__ == "__main__":
  uvicorn.run(
    "app.main:app",
    host=settings.host,
    port=settings.port,
    reload=True
  )
