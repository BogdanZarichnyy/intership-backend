from uuid import uuid4
from app.models.user import User


def make_user(**kwargs):
    user = User()

    user.id = kwargs.get("id", uuid4())
    user.email = kwargs.get("email", "test@test.com")
    user.username = kwargs.get("username", "testuser")
    user.hashed_password = kwargs.get("hashed_password", "hashed")
    user.provider = kwargs.get("provider", "local")
    user.provider_id = kwargs.get("provider_id")
    user.is_active = kwargs.get("is_active", True)

    return user


def make_user_dict(**kwargs):
    uid = kwargs.get("id", uuid4())

    return {
        "id": str(uid),
        "email": kwargs.get("email", "test@test.com"),
        "username": kwargs.get("username", "testuser"),
        "provider": kwargs.get("provider", "local"),
        "provider_id": kwargs.get("provider_id"),
        "is_active": kwargs.get("is_active", True),
    }
