import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

from app.main import create_app

@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)

# =========================
# Простий тест без моків
# =========================
def test_health_check_basic(client):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["ok", "error"]
    assert "message" in data
    assert "postgres" in data
    assert "redis" in data

# =========================
# Тест із моками для контролю результатів
# =========================
@pytest.mark.asyncio
async def test_health_check_mocked(client):
    # Мок для PostgreSQL
    with patch("app.routers.health.check_postgres", new_callable=AsyncMock) as mock_pg, \
         patch("app.routers.health.check_redis", new_callable=AsyncMock) as mock_redis:

        mock_pg.return_value = "ok"
        mock_redis.return_value = "ok"

        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["postgres"] == "ok"
        assert data["redis"] == "ok"
        assert data["status"] == "ok"

        # Тест, коли один із сервісів "error"
        mock_pg.return_value = "error"
        mock_redis.return_value = "ok"

        response = client.get("/")
        data = response.json()
        assert data["status"] == "error"
