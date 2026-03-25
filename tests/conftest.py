import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.models.user import User
from uuid import uuid4


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def fake_user():
    user = User()
    user.id = uuid4()
    user.email = "test@test.com"
    user.username = "testuser"
    user.is_active = True
    return user


@pytest.fixture(autouse=True)
def override_current_user(fake_user):
    from app.core.dependencies import get_current_user

    app.dependency_overrides[get_current_user] = lambda: fake_user
    yield
    app.dependency_overrides.clear()
