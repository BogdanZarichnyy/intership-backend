from unittest.mock import AsyncMock
from app.core.dependencies import (
    get_user_service,
    get_auth_service,
    get_current_user,
)

def setup_test_overrides(app, fake_user=None):
    """
    Централізовані overrides для всіх router tests
    """

    user_service = AsyncMock()
    auth_service = AsyncMock()

    # user service
    app.dependency_overrides[get_user_service] = lambda: user_service

    # auth service
    app.dependency_overrides[get_auth_service] = lambda: auth_service

    # current user (ключове)
    if fake_user:
        app.dependency_overrides[get_current_user] = lambda: fake_user

    return {
        "user_service": user_service,
        "auth_service": auth_service,
    }


def clear_overrides(app):
    app.dependency_overrides.clear()
