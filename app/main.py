from fastapi import FastAPI
import uvicorn

from app.routers.health import router as healthRouter
from app.core.middleware import setup_middlewares
from app.config import settings

def create_app() -> FastAPI: # Використовуємо factory pattern, щоб було легше тестувати
  app = FastAPI(title="Internship Backend")

  setup_middlewares(app)
  app.include_router(healthRouter)

  return app

app = create_app()

if __name__ == "__main__":
  uvicorn.run(
    "app.main:app",
    host=settings.host,
    port=settings.port,
    reload=True
  )
