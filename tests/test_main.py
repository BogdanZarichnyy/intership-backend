from fastapi.testclient import TestClient
from app.main import create_app

def test_health_check():
  app = create_app()
  client = TestClient(app)

  response = client.get("/")
  assert response.status_code == 200
  data = response.json()
  assert data["status"] in ["ok", "error"]
  assert "message" in data
  assert "postgres" in data
  assert "redis" in data
