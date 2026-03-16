import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock
from uuid import uuid4, UUID
from datetime import datetime, timezone

from app.main import app
from app.routers.company_member import CompanyAdminService
from app.schemas.company_member import CompanyMemberResponse

@pytest.fixture
async def client():
  async with AsyncClient(app=app, base_url="http://testserver") as ac:
    yield ac

@pytest.fixture
def user_uuid():
  return uuid4()

@pytest.fixture
def company_uuid():
  return uuid4()

def make_member_dict(uid=None, role="admin"):
  uid = uid or uuid4()
  now = datetime.now(timezone.utc)
  return {
    "company_id": str(uuid4()),
    "member_id": str(uid),
    "role": role,
    "created_at": now.isoformat(),
    "updated_at": now.isoformat(),
  }

@pytest.mark.asyncio
async def test_list_admins(client: AsyncClient, company_uuid):
  mock_service = AsyncMock()
  mock_service.get_list_admins.return_value = [make_member_dict()]
  app.dependency_overrides[CompanyAdminService] = lambda db=None: mock_service

  response = await client.get(f"/company-role/{company_uuid}")
  assert response.status_code == 200
  data = response.json()
  assert "admins" in data
  assert len(data["admins"]) == 1
  app.dependency_overrides = {}

@pytest.mark.asyncio
async def test_set_role_admin(client: AsyncClient, company_uuid, user_uuid):
  mock_service = AsyncMock()
  mock_service.change_member_role.return_value = make_member_dict(uid=user_uuid, role="admin")
  app.dependency_overrides[CompanyAdminService] = lambda db=None: mock_service

  response = await client.post(f"/company-role/{company_uuid}/admin/{user_uuid}")
  assert response.status_code == 200
  data = response.json()
  assert data["role"] == "admin"
  app.dependency_overrides = {}

@pytest.mark.asyncio
async def test_set_role_member(client: AsyncClient, company_uuid, user_uuid):
  mock_service = AsyncMock()
  mock_service.change_member_role.return_value = make_member_dict(uid=user_uuid, role="member")
  app.dependency_overrides[CompanyAdminService] = lambda db=None: mock_service

  response = await client.post(f"/company-role/{company_uuid}/member/{user_uuid}")
  assert response.status_code == 200
  data = response.json()
  assert data["role"] == "member"
  app.dependency_overrides = {}

@pytest.mark.asyncio
async def test_remove_admin(client: AsyncClient, company_uuid, user_uuid):
  mock_service = AsyncMock()
  mock_service.remove_admin.return_value = None
  app.dependency_overrides[CompanyAdminService] = lambda db=None: mock_service

  response = await client.delete(f"/company-role/{company_uuid}/remove/{user_uuid}")
  assert response.status_code == 200
  data = response.json()
  assert data["detail"] == "Admin removed successfully"
  app.dependency_overrides = {}
