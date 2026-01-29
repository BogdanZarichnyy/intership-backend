from fastapi import FastAPI
from app.routers.health import router as healthRouter
import uvicorn

app = FastAPI(title="Internship Backend")

app.include_router(healthRouter)

if __name__ == "__main__":
  uvicorn.run(
    "app.main:app",
    host="0.0.0.0",
    port=8000,
    reload=True
  )
