import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock
from uuid import uuid4
from datetime import datetime, timezone

from app.main import app
from app.models.user import User
from app.core.dependencies import get_user_service, get_current_user
from app.core.exceptions import (
    UserNotFound,
    ExistsEmail,
    ForbiddenAction,
)


# =========================
# CLIENT
# =========================

@pytest.fixture(scope="function")
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac


# =========================
# FAKE USER
# =========================

@pytest.fixture
def fake_user():
    user = User()
    user.id = uuid4()
    user.email = "test@test.com"
    user.username = "testuser"
    user.is_active = True
    return user


# =========================
# MOCK SERVICE + OVERRIDES
# =========================

@pytest.fixture
def mock_user_service(fake_user):
    mock = AsyncMock()

    app.dependency_overrides[get_user_service] = lambda: mock
    app.dependency_overrides[get_current_user] = lambda: fake_user

    yield mock

    app.dependency_overrides.pop(get_user_service, None)
    app.dependency_overrides.pop(get_current_user, None)


# =========================
# USER DICT FACTORY (API RESPONSE)
# =========================

def make_user_dict(uid=None, email="test@test.com", username="testuser", provider="local"):
    uid = uid or uuid4()
    now = datetime.now(timezone.utc)

    return {
        "id": str(uid),
        "email": email,
        "username": username,
        "provider": provider,
        "is_active": True,
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }


# =========================
# TESTS
# =========================

@pytest.mark.asyncio
async def test_create_user_success(client, mock_user_service):
    payload = {
        "email": "test@test.com",
        "username": "testuser",
        "password": "123456"
    }

    mock_user_service.create_new_user.return_value = make_user_dict()

    response = await client.post("/users/", json=payload)

    assert response.status_code == 201


@pytest.mark.asyncio
async def test_create_user_conflict(client, mock_user_service):
    payload = {
        "email": "test@test.com",
        "username": "testuser",
        "password": "123456"
    }

    mock_user_service.create_new_user.side_effect = ExistsEmail("test@test.com")

    response = await client.post("/users/", json=payload)

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_get_user_success(client, mock_user_service):
    uid = uuid4()

    mock_user_service.get_user_by_id.return_value = make_user_dict(uid=uid)

    response = await client.get(f"/users/{uid}")

    assert response.status_code == 200
    assert response.json()["id"] == str(uid)


@pytest.mark.asyncio
async def test_get_user_not_found(client, mock_user_service):
    mock_user_service.get_user_by_id.side_effect = UserNotFound()

    response = await client.get(f"/users/{uuid4()}")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_users(client, mock_user_service):
    mock_user_service.get_all_users.return_value = {
        "users": [make_user_dict()],
        "total": 1
    }

    response = await client.get("/users/?limit=10&offset=0")

    assert response.status_code == 200
    assert "users" in response.json()


@pytest.mark.asyncio
async def test_update_user_success(client, mock_user_service):
    uid = uuid4()

    mock_user_service.update_user_details.return_value = make_user_dict(
        uid=uid,
        username="newuser"
    )

    response = await client.patch(f"/users/{uid}", json={
        "username": "newuser"
    })

    assert response.status_code == 200
    assert response.json()["username"] == "newuser"


@pytest.mark.asyncio
async def test_update_user_forbidden(client, mock_user_service):
    mock_user_service.update_user_details.side_effect = ForbiddenAction()

    response = await client.patch(f"/users/{uuid4()}", json={
        "username": "newuser"
    })

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_delete_user_success(client, mock_user_service):
    mock_user_service.delete_user.return_value = None

    response = await client.delete(f"/users/{uuid4()}")

    assert response.status_code == 204


@pytest.mark.asyncio
async def test_delete_user_not_found(client, mock_user_service):
    mock_user_service.delete_user.side_effect = UserNotFound()

    response = await client.delete(f"/users/{uuid4()}")

    assert response.status_code == 404
