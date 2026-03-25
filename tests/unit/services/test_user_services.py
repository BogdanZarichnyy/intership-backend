import pytest
from unittest.mock import AsyncMock
from uuid import uuid4
from datetime import datetime, timezone

from app.services.user import UserService
from app.schemas.user import SignUpRequest, UserUpdate
from app.models.user import User
from app.core.exceptions import (
    UserNotFound,
    ExistsEmail,
    ExistsUsername,
    ForbiddenAction,
    InvalidPassword,
    MissingCurrentPassword,
)


@pytest.fixture
def repo():
    return AsyncMock()


@pytest.fixture
def service(repo):
    return UserService(repo)


@pytest.fixture
def user():
    u = User()
    u.id = uuid4()
    u.email = "test@test.com"
    u.username = "testuser"
    u.hashed_password = "hashed"
    u.is_active = True
    u.provider = "local"
    u.created_at = datetime.now(timezone.utc)
    u.updated_at = datetime.now(timezone.utc)
    return u


# CREATE

@pytest.mark.asyncio
async def test_create_user_success(service, repo, user):
    repo.get_user_by_email.return_value = None
    repo.get_user_by_username.return_value = None
    repo.create_user.return_value = user

    data = SignUpRequest(
        email="test@test.com",
        username="testuser",
        password="123456"
    )

    result = await service.create_new_user(data)

    assert result.id == user.id
    assert result.email == user.email
    assert result.username == user.username


@pytest.mark.asyncio
async def test_create_user_duplicate_email(service, repo, user):
    repo.get_user_by_email.return_value = user

    data = SignUpRequest(
        email="test@test.com",
        username="testuser",
        password="123456"
    )

    with pytest.raises(ExistsEmail):
        await service.create_new_user(data)


@pytest.mark.asyncio
async def test_create_user_duplicate_username(service, repo):
    repo.get_user_by_email.return_value = None
    repo.get_user_by_username.return_value = User()

    data = SignUpRequest(
        email="test@test.com",
        username="testuser",
        password="123456"
    )

    with pytest.raises(ExistsUsername):
        await service.create_new_user(data)


# GET

@pytest.mark.asyncio
async def test_get_user_success(service, repo, user):
    repo.get_user_by_id.return_value = user

    result = await service.get_user_by_id(user.id)

    assert result.id == user.id
    assert result.email == user.email


@pytest.mark.asyncio
async def test_get_user_not_found(service, repo):
    repo.get_user_by_id.return_value = None

    with pytest.raises(UserNotFound):
        await service.get_user_by_id(uuid4())


# UPDATE

@pytest.mark.asyncio
async def test_update_forbidden(service, repo, user):
    other = User()
    other.id = uuid4()

    with pytest.raises(ForbiddenAction):
        await service.update_user_details(
            user_id=user.id,
            update_data=UserUpdate(),
            current_user=other
        )


@pytest.mark.asyncio
async def test_update_not_found(service, repo, user):
    repo.get_user_by_id.return_value = None

    with pytest.raises(UserNotFound):
        await service.update_user_details(
            user_id=user.id,
            update_data=UserUpdate(),
            current_user=user
        )


@pytest.mark.asyncio
async def test_update_username_conflict(service, repo, user):
    repo.get_user_by_id.return_value = user
    repo.get_user_by_username.return_value = User()

    update = UserUpdate(username="newname")

    with pytest.raises(ExistsUsername):
        await service.update_user_details(user.id, update, user)


@pytest.mark.asyncio
async def test_update_password_missing_current(service, repo, user):
    repo.get_user_by_id.return_value = user

    update = UserUpdate(new_password="newpass")

    with pytest.raises(MissingCurrentPassword):
        await service.update_user_details(user.id, update, user)


@pytest.mark.asyncio
async def test_update_password_invalid(service, repo, user, monkeypatch):
    repo.get_user_by_id.return_value = user

    from app.services import user as user_module
    monkeypatch.setattr(user_module, "verify_password", lambda a, b: False)

    update = UserUpdate(
        current_password="wrong",
        new_password="newpass"
    )

    with pytest.raises(InvalidPassword):
        await service.update_user_details(user.id, update, user)


@pytest.mark.asyncio
async def test_update_password_success(service, repo, user, monkeypatch):
    repo.get_user_by_id.return_value = user
    repo.update_user_details.return_value = user

    from app.services import user as user_module
    monkeypatch.setattr(user_module, "verify_password", lambda a, b: True)
    monkeypatch.setattr(user_module, "hash_password", lambda x: "hashed_new")

    update = UserUpdate(
        current_password="ok",
        new_password="new"
    )

    result = await service.update_user_details(user.id, update, user)

    assert result.id == user.id
    repo.update_user_details.assert_called_once()


# DELETE

@pytest.mark.asyncio
async def test_delete_forbidden(service, repo):
    other = User()
    other.id = uuid4()

    with pytest.raises(ForbiddenAction):
        await service.delete_user(uuid4(), other)


@pytest.mark.asyncio
async def test_delete_not_found(service, repo, user):
    repo.get_user_by_id.return_value = None

    with pytest.raises(UserNotFound):
        await service.delete_user(user.id, user)


@pytest.mark.asyncio
async def test_delete_success(service, repo, user):
    repo.get_user_by_id.return_value = user

    await service.delete_user(user.id, user)

    repo.delete_user.assert_called_once_with(user.id)
