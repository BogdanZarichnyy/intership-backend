import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock
from uuid import uuid4
from datetime import datetime, timezone

from app.main import app
from app.models.user import User
from app.core.dependencies import get_company_service, get_current_user


# =========================
# CLIENT
# =========================

@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# =========================
# FAKE USER
# =========================

@pytest.fixture
def fake_user():
    user = User()
    user.id = uuid4()
    user.email = "test@test.com"
    return user


# =========================
# MOCK SERVICE
# =========================

@pytest.fixture
def mock_service(fake_user):
    mock = AsyncMock()

    app.dependency_overrides[get_company_service] = lambda: mock
    app.dependency_overrides[get_current_user] = lambda: fake_user

    yield mock

    app.dependency_overrides.clear()


# =========================
# HELPERS
# =========================

def make_company_dict(company_id=None):
    now = datetime.now(timezone.utc)
    return {
        "id": str(company_id or uuid4()),
        "name": "Test Company",
        "description": "desc",
        "owner_id": str(uuid4()),
        "is_visible": True,
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }


# =========================
# TESTS
# =========================

@pytest.mark.asyncio
async def test_get_all_companies(client, mock_service):
    mock_service.get_all_companies.return_value = {
        "companies": [make_company_dict()],
        "total": 1
    }

    res = await client.get("/companies/?limit=10&offset=0")

    assert res.status_code == 200
    assert "companies" in res.json()


@pytest.mark.asyncio
async def test_get_company_by_id(client, mock_service):
    cid = uuid4()
    mock_service.get_company_by_id.return_value = make_company_dict(cid)

    res = await client.get(f"/companies/{cid}")

    assert res.status_code == 200
    assert res.json()["id"] == str(cid)


@pytest.mark.asyncio
async def test_create_company(client, mock_service):
    mock_service.create_company.return_value = make_company_dict()

    res = await client.post("/companies/", json={
        "name": "Test Company",
        "description": "desc"
    })

    assert res.status_code == 201


@pytest.mark.asyncio
async def test_update_company(client, mock_service):
    cid = uuid4()
    mock_service.update_company.return_value = make_company_dict(cid)

    res = await client.patch(f"/companies/{cid}", json={
        "name": "Updated"
    })

    assert res.status_code == 200


@pytest.mark.asyncio
async def test_delete_company(client, mock_service):
    mock_service.delete_company.return_value = None

    res = await client.delete(f"/companies/{uuid4()}")

    assert res.status_code == 204
