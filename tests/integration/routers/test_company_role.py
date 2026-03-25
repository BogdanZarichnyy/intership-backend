import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock
from uuid import uuid4
from datetime import datetime, timezone

from app.main import app
from app.routers.company_role import get_company_admin_service
from app.core.dependencies import get_current_user


class MockUser:
    def __init__(self, id):
        self.id = id


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


def make_role_response(company_id, member_id, role):
    now = datetime.now(timezone.utc).isoformat()
    return {
        "member_id": str(member_id),
        "company_id": str(company_id),
        "role": role,
        "created_at": now,
        "updated_at": now,
    }


# -------------------------
# list_admins
# -------------------------
@pytest.mark.asyncio
async def test_list_admins(client):
    mock = AsyncMock()
    mock.get_list_admins.return_value = {"admins": []}

    app.dependency_overrides[get_company_admin_service] = lambda: mock
    app.dependency_overrides[get_current_user] = lambda: MockUser(uuid4())

    res = await client.get(f"/company-role/{uuid4()}")
    assert res.status_code == 200

    app.dependency_overrides.clear()


# -------------------------
# set_role_admin
# -------------------------
@pytest.mark.asyncio
async def test_set_role_admin(client):
    company_id = uuid4()
    member_id = uuid4()

    mock = AsyncMock()
    mock.change_member_role.return_value = make_role_response(
        company_id, member_id, "admin"
    )

    app.dependency_overrides[get_company_admin_service] = lambda: mock
    app.dependency_overrides[get_current_user] = lambda: MockUser(uuid4())

    res = await client.patch(f"/company-role/{company_id}/admin/{member_id}")
    assert res.status_code == 200

    app.dependency_overrides.clear()


# -------------------------
# set_role_member
# -------------------------
@pytest.mark.asyncio
async def test_set_role_member(client):
    company_id = uuid4()
    member_id = uuid4()

    mock = AsyncMock()
    mock.change_member_role.return_value = make_role_response(
        company_id, member_id, "member"
    )

    app.dependency_overrides[get_company_admin_service] = lambda: mock
    app.dependency_overrides[get_current_user] = lambda: MockUser(uuid4())

    res = await client.patch(f"/company-role/{company_id}/member/{member_id}")
    assert res.status_code == 200

    app.dependency_overrides.clear()


# -------------------------
# remove_admin
# -------------------------
@pytest.mark.asyncio
async def test_remove_admin(client):
    mock = AsyncMock()

    app.dependency_overrides[get_company_admin_service] = lambda: mock
    app.dependency_overrides[get_current_user] = lambda: MockUser(uuid4())

    res = await client.delete(f"/company-role/{uuid4()}/remove/{uuid4()}")
    assert res.status_code == 204

    app.dependency_overrides.clear()
