import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock
from uuid import uuid4
from datetime import datetime, timezone

from app.main import app
from app.core.dependencies import get_invitation_service, get_current_user


class MockUser:
    def __init__(self, id):
        self.id = id


def fake_invitation():
    return {
        "id": str(uuid4()),
        "company_id": str(uuid4()),
        "invited_user_id": str(uuid4()),
        "invited_by": str(uuid4()),
        "status": "pending",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


# -------------------------
# create invitation
# -------------------------

@pytest.mark.asyncio
async def test_create_invitation(client):
    mock = AsyncMock()
    mock.company_join_initialization.return_value = fake_invitation()

    app.dependency_overrides[get_invitation_service] = lambda: mock
    app.dependency_overrides[get_current_user] = lambda: MockUser(uuid4())

    res = await client.post(f"/company-invitations/{uuid4()}")

    assert res.status_code == 201


# -------------------------
# my requests
# -------------------------

@pytest.mark.asyncio
async def test_my_requests(client):
    mock = AsyncMock()
    mock.get_user_requests.return_value = []

    app.dependency_overrides[get_invitation_service] = lambda: mock
    app.dependency_overrides[get_current_user] = lambda: MockUser(uuid4())

    res = await client.get("/company-invitations/my-requests")

    assert res.status_code == 200


# -------------------------
# my invitations
# -------------------------

@pytest.mark.asyncio
async def test_my_invitations(client):
    mock = AsyncMock()
    mock.get_user_received_invitations.return_value = []

    app.dependency_overrides[get_invitation_service] = lambda: mock
    app.dependency_overrides[get_current_user] = lambda: MockUser(uuid4())

    res = await client.get("/company-invitations/my-invitations")

    assert res.status_code == 200


# -------------------------
# accept
# -------------------------

@pytest.mark.asyncio
async def test_accept(client):
    mock = AsyncMock()
    mock.accept_invitation.return_value = fake_invitation()

    app.dependency_overrides[get_invitation_service] = lambda: mock
    app.dependency_overrides[get_current_user] = lambda: MockUser(uuid4())

    res = await client.patch(f"/company-invitations/{uuid4()}/accept")

    assert res.status_code == 200


# -------------------------
# decline
# -------------------------

@pytest.mark.asyncio
async def test_decline(client):
    mock = AsyncMock()
    mock.decline_invitation.return_value = fake_invitation()

    app.dependency_overrides[get_invitation_service] = lambda: mock
    app.dependency_overrides[get_current_user] = lambda: MockUser(uuid4())

    res = await client.patch(f"/company-invitations/{uuid4()}/decline")

    assert res.status_code == 200


# -------------------------
# cancel
# -------------------------

@pytest.mark.asyncio
async def test_cancel(client):
    mock = AsyncMock()
    mock.cancel_invitation.return_value = fake_invitation()

    app.dependency_overrides[get_invitation_service] = lambda: mock
    app.dependency_overrides[get_current_user] = lambda: MockUser(uuid4())

    res = await client.patch(f"/company-invitations/{uuid4()}/cancel")

    assert res.status_code == 200
