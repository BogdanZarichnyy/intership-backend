from fastapi import FastAPI
from app.routers.health import router as healthRouter
from app.config import settings
import uvicorn

app = FastAPI(title="Internship Backend")

app.include_router(healthRouter)

if __name__ == "__main__":
  uvicorn.run(
    "app.main:app",
      host=settings.host,
      port=settings.port,
    reload=True
  )
