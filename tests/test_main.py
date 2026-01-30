from fastapi.testclient import TestClient
from fastapi import FastAPI
from app.routers.health import router  # без імпорту app.main

app = FastAPI()
app.include_router(router)

client = TestClient(app)

def test_health_check():
  response = client.get("/")
  assert response.status_code == 200
  assert response.json() == {
    "status": "ok",
    "message": "working"
  }
