from fastapi import FastAPI
from app.routers.health import router as healthRouter

app = FastAPI(title="Internship Backend")

app.include_router(healthRouter)
