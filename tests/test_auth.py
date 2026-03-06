import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from app.main import app
from app.services.user import UserService
from app.routers.auth import get_current_user

# --- Фікстура клієнта ---
@pytest.fixture
async def client():
  async with AsyncClient(app=app, base_url="http://testserver") as ac:
    yield ac

# --- MOCK клас користувача ---
class MockUser:
  def __init__(self, id, provider="local", is_active=True):
    self.id = id
    self.provider = provider
    self.is_active = is_active
    self.email = "test@test.com"
    self.hashed_password = "hashed"

# --- Тести для /auth/login ---
@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
  mock_service = AsyncMock()
  mock_service.authenticate_user.return_value = {
    "access_token": "fake-token",
    "refresh_token": "fake-refresh",
    "token_type": "bearer"
  }
  app.dependency_overrides[UserService] = lambda db=None: mock_service

  response = await client.post("/auth/login", json={
    "email": "test@test.com",
    "password": "password123"
  })
  assert response.status_code == 200
  data = response.json()
  assert "access_token" in data
  app.dependency_overrides = {}

@pytest.mark.asyncio
async def test_login_failure(client: AsyncClient):
  mock_service = AsyncMock()
  mock_service.authenticate_user.side_effect = Exception("Invalid credentials")
  app.dependency_overrides[UserService] = lambda db=None: mock_service

  response = await client.post("/auth/login", json={
    "email": "test@test.com",
    "password": "wrongpass"
  })
  assert response.status_code in (400, 401)
  app.dependency_overrides = {}

# --- Тест logout ---
@pytest.mark.asyncio
async def test_logout_local_user(client):
  app.dependency_overrides[get_current_user] = lambda: MockUser(id=uuid4(), provider="local")
  response = await client.post("/auth/logout")
  assert response.status_code == 200
  assert "Logged out successfully" in response.json()["message"]
  app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_logout_auth0_user(client):
  app.dependency_overrides[get_current_user] = lambda: MockUser(id=uuid4(), provider="auth0")
  response = await client.post("/auth/logout")
  assert response.status_code in (307, 308)  # редірект
  app.dependency_overrides.clear()

# --- Тест refresh token ---
@pytest.mark.asyncio
async def test_refresh_token_success(client):
  fake_token = "fake_refresh_token"
  user_id = str(uuid4())
  app.dependency_overrides[get_current_user] = lambda: MockUser(id=uuid4())

  with patch("app.routers.auth.decode_token") as mock_decode:
    mock_decode.return_value = {"sub": user_id, "type": "refresh"}
    with patch("app.routers.auth.UserService.get_user_by_id", new_callable=AsyncMock) as mock_user_service:
      mock_user_service.return_value = MockUser(id=user_id)
      response = await client.post("/auth/refresh", headers={"Authorization": f"Bearer {fake_token}"})
      assert response.status_code == 200
      data = response.json()
      assert "access_token" in data
      assert data["token_type"] == "bearer"
  app.dependency_overrides.clear()

# --- Тест auth0 callback ---
@pytest.mark.asyncio
async def test_auth0_callback(client):
  fake_data = {
    "access_token": "access",
    "id_token": "id_token",
    "scope": "openid profile email",
    "expires_in": 86400,
    "token_type": "Bearer"
  }
  with patch("app.routers.auth.decode_auth0_token") as mock_decode_auth0:
    mock_decode_auth0.return_value = {
      "email": "auth0@test.com",
      "sub": "auth0|12345",
      "email_verified": True
    }
    with patch("app.routers.auth.UserService.get_user_by_provider_id", new_callable=AsyncMock) as mock_by_provider:
      mock_by_provider.return_value = None
      with patch("app.routers.auth.UserService.get_user_by_email", new_callable=AsyncMock) as mock_by_email:
        mock_by_email.return_value = None
        with patch("app.routers.auth.UserService.create_new_user", new_callable=AsyncMock) as mock_create:
          mock_create.return_value = MockUser(id=uuid4(), provider="auth0")
          response = await client.post("/auth/callback", json=fake_data)
          assert response.status_code == 200
          data = response.json()
          assert "access_token" in data
          assert "refresh_token" in data
          assert data["token_type"] == "bearer"
