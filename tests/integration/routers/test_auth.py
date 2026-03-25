import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock

from app.main import app
from app.core.dependencies import get_auth_service, get_current_user


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# =========================
# LOGIN
# =========================

@pytest.mark.asyncio
async def test_login(client):
    mock = AsyncMock()
    mock.login.return_value = {
        "access_token": "a",
        "refresh_token": "b",
        "token_type": "bearer"
    }

    app.dependency_overrides[get_auth_service] = lambda: mock

    res = await client.post("/auth/login", json={
        "email": "test@test.com",
        "password": "123"
    })

    assert res.status_code == 200
    assert "access_token" in res.json()

    app.dependency_overrides.clear()


# =========================
# LOGOUT LOCAL
# =========================

class MockUser:
    def __init__(self):
        self.provider = "local"


@pytest.mark.asyncio
async def test_logout_local(client):
    app.dependency_overrides[get_current_user] = lambda: MockUser()

    res = await client.post("/auth/logout")

    assert res.status_code == 200

    app.dependency_overrides.clear()


# =========================
# REFRESH
# =========================

@pytest.mark.asyncio
async def test_refresh(client):
    mock = AsyncMock()
    mock.refresh_access_token.return_value = {"access_token": "x"}

    app.dependency_overrides[get_auth_service] = lambda: mock

    res = await client.post(
        "/auth/refresh",
        headers={"Authorization": "Bearer token"}
    )

    assert res.status_code == 200
    assert "access_token" in res.json()

    app.dependency_overrides.clear()
