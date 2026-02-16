import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock

from app.main import app
from app.routers.user import UserService

@pytest.fixture
async def client():
  async with AsyncClient(app=app, base_url="http://testserver", transport=None) as ac:
    yield ac

@pytest.mark.asyncio
async def test_create_user(client: AsyncClient):
  mock_service = AsyncMock()
  mock_service.create_new_user.return_value = {
    "id": 1,
    "email": "test@test.com",
    "username": "testuser",
    "is_active": True
  }
  app.dependency_overrides[UserService] = lambda: mock_service
  response = await client.post("/users/", json={
    "email": "test@test.com",
    "username": "testuser",
    "password": "password123"
  })
  assert response.status_code == 201
  data = response.json()
  assert data["email"] == "test@test.com"
  assert data["username"] == "testuser"
  app.dependency_overrides = {}

@pytest.mark.asyncio
async def test_create_user_duplicate_email(client: AsyncClient):
  mock_service = AsyncMock()
  mock_service.create_new_user.side_effect = Exception("User exists")
  app.dependency_overrides[UserService] = lambda: mock_service
  response = await client.post("/users/", json={
    "email": "test@test.com",
    "username": "testuser",
    "password": "password123"
  })
  # Перевіряємо, що помилка обробляється через HTTPException
  assert response.status_code in (400, 409)
  app.dependency_overrides = {}

@pytest.mark.asyncio
async def test_get_users(client: AsyncClient):
  mock_service = AsyncMock()
  mock_service.get_all_users.return_value = {
    "users": [],
    "total": 0
  }
  app.dependency_overrides[UserService] = lambda: mock_service
  response = await client.get("/users/?limit=10&offset=0")
  assert response.status_code == 200
  data = response.json()
  assert "users" in data
  assert "total" in data
  app.dependency_overrides = {}

@pytest.mark.asyncio
async def test_get_user_by_id(client: AsyncClient):
  mock_service = AsyncMock()
  mock_service.get_user_by_id.return_value = {
    "id": 1,
    "email": "test@test.com",
    "username": "testuser",
    "is_active": True
  }
  app.dependency_overrides[UserService] = lambda: mock_service
  response = await client.get("/users/1")
  assert response.status_code == 200
  data = response.json()
  assert data["id"] == 1
  app.dependency_overrides = {}

@pytest.mark.asyncio
async def test_get_user_not_found(client: AsyncClient):
  mock_service = AsyncMock()
  mock_service.get_user_by_id.return_value = None
  app.dependency_overrides[UserService] = lambda: mock_service
  response = await client.get("/users/999")
  assert response.status_code == 404
  app.dependency_overrides = {}

@pytest.mark.asyncio
async def test_update_user(client: AsyncClient):
  mock_service = AsyncMock()
  mock_service.get_user_by_id.return_value = {}
  mock_service.update_user.return_value = {
    "id": 1,
    "email": "new@test.com",
    "username": "newuser",
    "is_active": True
  }
  app.dependency_overrides[UserService] = lambda: mock_service
  response = await client.put("/users/1", json={
    "email": "new@test.com",
    "username": "newuser"
  })
  assert response.status_code == 200
  data = response.json()
  assert data["email"] == "new@test.com"
  app.dependency_overrides = {}

@pytest.mark.asyncio
async def test_delete_user(client: AsyncClient):
  mock_service = AsyncMock()
  mock_service.get_user_by_id.return_value = {}
  mock_service.delete_user.return_value = None
  app.dependency_overrides[UserService] = lambda: mock_service
  response = await client.delete("/users/1")
  assert response.status_code == 204
  app.dependency_overrides = {}
