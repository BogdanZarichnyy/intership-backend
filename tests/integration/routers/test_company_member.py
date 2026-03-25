import pytest
from httpx import AsyncClient, ASGITransport
from uuid import uuid4
from unittest.mock import AsyncMock

from app.main import app
from app.core.dependencies import get_current_user
from app.routers.company_member import get_company_member_service


# Простий мок користувача
class MockUser:
    def __init__(self, id, owner=True, member=True):
        self.id = id
        self._is_owner = owner
        self._is_member = member

    def is_owner_of_company(self, company_id):
        return self._is_owner

    def is_member_of_company(self, company_id):
        return self._is_member


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac


# -------------------------
# REMOVE MEMBER
# -------------------------
@pytest.mark.asyncio
async def test_remove_member_by_company_owner(client):
    company_id = uuid4()
    member_id = uuid4()

    mock_service = AsyncMock()
    mock_service.remove_member.return_value = None

    app.dependency_overrides[get_company_member_service] = lambda: mock_service
    app.dependency_overrides[get_current_user] = lambda: MockUser(id=uuid4(), owner=True)

    response = await client.delete(
        f"/company-members/{company_id}/remove-member/{member_id}"
    )

    assert response.status_code == 204
    assert response.content == b""

    app.dependency_overrides.clear()


# -------------------------
# LEAVE COMPANY
# -------------------------
@pytest.mark.asyncio
async def test_leave_company_by_member(client):
    company_id = uuid4()
    member_id = uuid4()

    mock_service = AsyncMock()
    mock_service.leave_company.return_value = None

    app.dependency_overrides[get_company_member_service] = lambda: mock_service
    app.dependency_overrides[get_current_user] = lambda: MockUser(id=uuid4(), member=True)

    response = await client.delete(
        f"/company-members/{company_id}/member-leave/{member_id}"
    )

    assert response.status_code == 204
    assert response.content == b""

    app.dependency_overrides.clear()


# -------------------------
# GET MEMBERS
# -------------------------
@pytest.mark.asyncio
async def test_get_members_of_company(client):
    company_id = uuid4()
    member_id = uuid4()

    mock_service = AsyncMock()
    mock_service.get_members.return_value = [
      {
        "member_id": str(member_id),
        "company_id": str(company_id),
        "role": "member",
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-01-01T00:00:00Z",
      }
    ]

    app.dependency_overrides[get_company_member_service] = lambda: mock_service
    app.dependency_overrides[get_current_user] = lambda: MockUser(id=uuid4())

    response = await client.get(
        f"/company-members/{company_id}/members?limit=50&offset=0"
    )

    assert response.status_code == 200
    data = response.json()

    assert isinstance(data, list)
    assert data[0]["member_id"] == str(member_id)
    assert data[0]["company_id"] == str(company_id)

    app.dependency_overrides.clear()
