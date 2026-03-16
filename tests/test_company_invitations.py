import pytest
from httpx import AsyncClient
from uuid import uuid4
from unittest.mock import AsyncMock

from app.main import app
from app.routers.company_invitation import get_invitation_service, get_current_user

# Мок користувача
class MockUser:
  def __init__(self, id):
    self.id = id

@pytest.fixture
async def client():
  async with AsyncClient(app=app, base_url="http://testserver") as ac:
    yield ac

@pytest.mark.asyncio
async def test_invite_user(client):
  company_id = uuid4()
  user_id = uuid4()
  mock_service = AsyncMock()
  mock_service.company_join_initialization.return_value = {"id": str(uuid4())}

  app.dependency_overrides[get_invitation_service] = lambda: mock_service
  app.dependency_overrides[get_current_user] = lambda: MockUser(id=uuid4())

  response = await client.post(f"/company-invitations/{company_id}/{user_id}")
  assert response.status_code == 200

  app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_get_my_requests(client):
  mock_service = AsyncMock()
  mock_service.get_user_requests.return_value = [{"id": str(uuid4())}]

  app.dependency_overrides[get_invitation_service] = lambda: mock_service
  app.dependency_overrides[get_current_user] = lambda: MockUser(id=uuid4())

  response = await client.get("/company-invitations/my-requests")
  assert response.status_code == 200
  data = response.json()
  assert isinstance(data, list)

  app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_get_my_invitations(client):
  mock_service = AsyncMock()
  mock_service.get_user_received_invitations.return_value = [{"id": str(uuid4())}]

  app.dependency_overrides[get_invitation_service] = lambda: mock_service
  app.dependency_overrides[get_current_user] = lambda: MockUser(id=uuid4())

  response = await client.get("/company-invitations/my-invitations")
  assert response.status_code == 200
  data = response.json()
  assert isinstance(data, list)

  app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_get_company_invited(client):
  company_id = uuid4()
  mock_service = AsyncMock()
  mock_service.get_company_invited_users.return_value = [{"id": str(uuid4())}]

  app.dependency_overrides[get_invitation_service] = lambda: mock_service
  app.dependency_overrides[get_current_user] = lambda: MockUser(id=uuid4())

  response = await client.get(f"/company-invitations/company/{company_id}/invited")
  assert response.status_code == 200
  data = response.json()
  assert isinstance(data, list)

  app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_get_company_requests(client):
  company_id = uuid4()
  mock_service = AsyncMock()
  mock_service.get_company_membership_requests.return_value = [{"id": str(uuid4())}]

  app.dependency_overrides[get_invitation_service] = lambda: mock_service
  app.dependency_overrides[get_current_user] = lambda: MockUser(id=uuid4())

  response = await client.get(f"/company-invitations/company/{company_id}/requests")
  assert response.status_code == 200
  data = response.json()
  assert isinstance(data, list)

  app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_accept_invitation(client):
  invitation_id = uuid4()
  mock_service = AsyncMock()
  mock_service.accept_invitation.return_value = {"id": str(invitation_id)}

  app.dependency_overrides[get_invitation_service] = lambda: mock_service
  app.dependency_overrides[get_current_user] = lambda: MockUser(id=uuid4())

  response = await client.put(f"/company-invitations/{invitation_id}/accept")
  assert response.status_code == 200

  app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_decline_invitation(client):
  invitation_id = uuid4()
  mock_service = AsyncMock()
  mock_service.decline_invitation.return_value = {"id": str(invitation_id)}

  app.dependency_overrides[get_invitation_service] = lambda: mock_service
  app.dependency_overrides[get_current_user] = lambda: MockUser(id=uuid4())

  response = await client.put(f"/company-invitations/{invitation_id}/decline")
  assert response.status_code == 200

  app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_cancel_invitation(client):
  invitation_id = uuid4()
  mock_service = AsyncMock()
  mock_service.cancel_invitation.return_value = {"id": str(invitation_id)}

  app.dependency_overrides[get_invitation_service] = lambda: mock_service
  app.dependency_overrides[get_current_user] = lambda: MockUser(id=uuid4())

  response = await client.put(f"/company-invitations/{invitation_id}/cancel")
  assert response.status_code == 200

  app.dependency_overrides.clear()
