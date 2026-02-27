import pytest
from httpx import AsyncClient
from uuid import uuid4
from unittest.mock import AsyncMock

from app.main import app
from app.routers.company import get_company_service, get_current_user

class MockUser:
  def __init__(self, id):
    self.id = id

@pytest.fixture
async def client():
  async with AsyncClient(app=app, base_url="http://testserver") as ac:
    yield ac

@pytest.mark.asyncio
async def test_get_all_companies(client):
  mock_service = AsyncMock()
  mock_service.get_all_companies.return_value = {
    "companies": [{"id": str(uuid4()), "name": "Test"}],
    "total": 1
  }
  app.dependency_overrides[get_company_service] = lambda: mock_service
  app.dependency_overrides[get_current_user] = lambda: MockUser(id=uuid4())

  response = await client.get("/companies/?limit=10&offset=0")
  assert response.status_code == 200
  data = response.json()
  assert "companies" in data
  assert "total" in data

  app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_get_company_by_id(client):
  company_id = uuid4()
  owner_id = uuid4()
  mock_service = AsyncMock()
  mock_service.get_company_by_id.return_value = {
    "id": str(company_id),
    "name": "Test Company",
    "owner_id": str(owner_id),
    "is_visible": True
  }
  app.dependency_overrides[get_company_service] = lambda: mock_service
  app.dependency_overrides[get_current_user] = lambda: MockUser(id=owner_id)

  response = await client.get(f"/companies/{company_id}")
  assert response.status_code == 200
  data = response.json()
  assert data["id"] == str(company_id)
  assert data["name"] == "Test Company"

  app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_create_company(client):
  owner_id = uuid4()
  mock_service = AsyncMock()
  company_id = uuid4()
  mock_service.create_company.return_value = {
    "id": str(company_id),
    "name": "New Company",
    "owner_id": str(owner_id),
    "is_visible": True
  }
  app.dependency_overrides[get_company_service] = lambda: mock_service
  app.dependency_overrides[get_current_user] = lambda: MockUser(id=owner_id)

  response = await client.post("/companies/", json={
    "name": "New Company",
    "description": "Description",
    "is_visible": True
  })
  assert response.status_code == 200
  data = response.json()
  assert data["id"] == str(company_id)
  assert data["name"] == "New Company"

  app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_update_company(client):
  company_id = uuid4()
  owner_id = uuid4()
  mock_service = AsyncMock()
  mock_service.get_company_by_id.return_value = {
    "id": str(company_id),
    "name": "Old Name",
    "owner_id": str(owner_id),
    "is_visible": True
  }
  mock_service.update_company.return_value = {
    "id": str(company_id),
    "name": "Updated Name",
    "owner_id": str(owner_id),
    "is_visible": True
  }
  app.dependency_overrides[get_company_service] = lambda: mock_service
  app.dependency_overrides[get_current_user] = lambda: MockUser(id=owner_id)

  response = await client.put(f"/companies/{company_id}", json={
    "name": "Updated Name",
    "description": "New Description",
    "is_visible": False
  })
  assert response.status_code == 200
  data = response.json()
  assert data["name"] == "Updated Name"

  app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_delete_company(client):
  company_id = uuid4()
  owner_id = uuid4()
  mock_service = AsyncMock()
  mock_service.get_company_by_id.return_value = {
    "id": str(company_id),
    "owner_id": str(owner_id)
  }
  mock_service.delete_company.return_value = None

  app.dependency_overrides[get_company_service] = lambda: mock_service
  app.dependency_overrides[get_current_user] = lambda: MockUser(id=owner_id)

  response = await client.delete(f"/companies/{company_id}")
  assert response.status_code == 200

  app.dependency_overrides.clear()
