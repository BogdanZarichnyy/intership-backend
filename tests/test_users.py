import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock
from uuid import uuid4
from datetime import datetime, timezone

from app.main import app
from app.routers.user import UserService

@pytest.fixture
async def client():
  async with AsyncClient(app=app, base_url="http://testserver") as ac:
    yield ac

@pytest.fixture
def user_uuid():
  return uuid4()

def make_user_dict(email="test@test.com", username="testuser", provider="local", uid=None):
  uid = uid or uuid4()
  now = datetime.now(timezone.utc)
  return {
    "id": str(uid),
    "email": email,
    "username": username,
    "is_active": True,
    "provider": provider,
    "created_at": now.isoformat(),
    "updated_at": now.isoformat(),
  }

@pytest.mark.asyncio
async def test_create_user(client: AsyncClient):
  mock_service = AsyncMock()
  mock_service.create_new_user.return_value = make_user_dict()
  app.dependency_overrides[UserService] = lambda: mock_service

  response = await client.post("/users/", json={
    "email": "test@test.com",
    "username": "testuser",
    "password": "password123",
  })
  assert response.status_code == 201
  data = response.json()
  assert data["email"] == "test@test.com"
  assert data["username"] == "testuser"
  assert data["provider"] == "local"
  app.dependency_overrides = {}

@pytest.mark.asyncio
async def test_create_user_with_provider(client: AsyncClient):
  mock_service = AsyncMock()
  mock_service.create_new_user.return_value = make_user_dict(provider="auth0")
  app.dependency_overrides[UserService] = lambda: mock_service

  response = await client.post("/users/", json={
    "email": "oauth@test.com",
    "username": "oauthuser",
    "provider": "auth0",
    "provider_id": "google-oauth2|123456789",
  })
  assert response.status_code == 201
  data = response.json()
  assert data["provider"] == "auth0"
  app.dependency_overrides = {}

@pytest.mark.asyncio
async def test_create_user_duplicate_email(client: AsyncClient):
  mock_service = AsyncMock()
  mock_service.create_new_user.side_effect = Exception("User exists")
  app.dependency_overrides[UserService] = lambda: mock_service

  response = await client.post("/users/", json={
    "email": "test@test.com",
    "username": "testuser",
    "password": "password123",
  })
  assert response.status_code in (400, 409)
  app.dependency_overrides = {}

@pytest.mark.asyncio
async def test_get_user_by_id(client: AsyncClient, user_uuid):
  mock_service = AsyncMock()
  mock_service.get_user_by_id.return_value = make_user_dict(uid=user_uuid)
  app.dependency_overrides[UserService] = lambda: mock_service

  response = await client.get(f"/users/{user_uuid}")
  assert response.status_code == 200
  data = response.json()
  assert data["id"] == str(user_uuid)
  app.dependency_overrides = {}

@pytest.mark.asyncio
async def test_get_user_not_found(client: AsyncClient, user_uuid):
  mock_service = AsyncMock()
  mock_service.get_user_by_id.return_value = None
  app.dependency_overrides[UserService] = lambda: mock_service

  response = await client.get(f"/users/{user_uuid}")
  assert response.status_code == 404
  app.dependency_overrides = {}

@pytest.mark.asyncio
async def test_get_users(client: AsyncClient):
  mock_service = AsyncMock()
  mock_service.get_all_users.return_value = {
    "users": [make_user_dict()],
    "total": 1
  }
  app.dependency_overrides[UserService] = lambda: mock_service

  response = await client.get("/users/?limit=10&offset=0")
  assert response.status_code == 200
  data = response.json()
  assert "users" in data
  assert "total" in data
  app.dependency_overrides = {}

@pytest.mark.asyncio
async def test_update_user(client: AsyncClient, user_uuid):
  mock_service = AsyncMock()
  mock_service.get_user_by_id.return_value = make_user_dict(uid=user_uuid)
  mock_service.update_user_details.return_value = make_user_dict(
    email="new@test.com", username="newuser", uid=user_uuid
  )
  app.dependency_overrides[UserService] = lambda: mock_service

  response = await client.put(f"/users/{user_uuid}", json={
    "email": "new@test.com",
    "username": "newuser",
  })
  assert response.status_code == 200
  data = response.json()
  assert data["email"] == "new@test.com"
  app.dependency_overrides = {}

@pytest.mark.asyncio
async def test_delete_user(client: AsyncClient, user_uuid):
  mock_service = AsyncMock()
  mock_service.get_user_by_id.return_value = make_user_dict(uid=user_uuid)
  mock_service.delete_user.return_value = None
  app.dependency_overrides[UserService] = lambda: mock_service

  response = await client.delete(f"/users/{user_uuid}")
  assert response.status_code == 204
  app.dependency_overrides = {}
