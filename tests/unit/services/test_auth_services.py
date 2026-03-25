import pytest
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from app.services.auth import AuthService
from app.models.user import User
from app.core.exceptions import (
    InvalidCredentials,
    UserDisabled,
    UserNotFound,
    InvalidToken,
    InvalidTokenType,
    InvalidTokenPayload,
    MissingIdToken,
    InvalidAuth0Token,
)

@pytest.fixture
def repo():
    return AsyncMock()

@pytest.fixture
def service(repo):
    return AuthService(repo)

@pytest.fixture
def user():
    u = User()
    u.id = uuid4()
    u.email = "test@test.com"
    u.username = "test"
    u.provider = "local"
    u.is_active = True
    u.hashed_password = "hashed"
    return u


# =========================
# LOGIN
# =========================

@pytest.mark.asyncio
async def test_login_success(service, repo, user):
    repo.get_user_by_email.return_value = user

    with patch("app.services.auth.verify_password", return_value=True), \
         patch("app.services.auth.create_access_token", return_value="access"), \
         patch("app.services.auth.create_refresh_token", return_value="refresh"):

        result = await service.login("test@test.com", "123")

        assert result["access_token"] == "access"
        assert result["refresh_token"] == "refresh"


@pytest.mark.asyncio
async def test_login_invalid(service, repo):
    repo.get_user_by_email.return_value = None

    with pytest.raises(InvalidCredentials):
        await service.login("x", "y")


# =========================
# REFRESH
# =========================

@pytest.mark.asyncio
async def test_refresh_success(service, repo, user):
    repo.get_user_by_id.return_value = user

    with patch("app.services.auth.decode_token", return_value={
        "sub": str(user.id),
        "type": "refresh"
    }), patch("app.services.auth.create_access_token", return_value="new_access"):

        result = await service.refresh_access_token("token")

        assert result["access_token"] == "new_access"


@pytest.mark.asyncio
async def test_refresh_invalid_token(service):
    with patch("app.services.auth.decode_token", side_effect=Exception):
        with pytest.raises(InvalidToken):
            await service.refresh_access_token("bad")


# =========================
# GET CURRENT USER
# =========================

@pytest.mark.asyncio
async def test_get_current_user(service, repo, user):
    repo.get_user_by_id.return_value = user

    with patch("app.services.auth.decode_token", return_value={
        "sub": str(user.id),
        "type": "access"
    }):

        result = await service.get_current_user_from_token("token")

        assert result.id == user.id


# =========================
# AUTH0 CALLBACK
# =========================

@pytest.mark.asyncio
async def test_auth0_missing_id_token(service):
    with pytest.raises(MissingIdToken):
        await service.handle_auth0_callback(None)


@pytest.mark.asyncio
async def test_auth0_invalid(service):
    with patch("app.services.auth.decode_auth0_token", side_effect=Exception):
        with pytest.raises(InvalidAuth0Token):
            await service.handle_auth0_callback("token")
