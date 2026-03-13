from uuid import UUID
from app.core.security import (
  verify_password, 
  create_access_token, 
  create_refresh_token, 
  decode_token
)
from app.core.auth0 import decode_auth0_token
from app.core.exceptions import (
  InvalidCredentials,
  InvalidToken,
  InvalidTokenType,
  InvalidTokenPayload,
  UserDisabled,
  UserNotFound,
  MissingIdToken,
  InvalidAuth0Token,
  EmailNotVerified,
  EmailNotFoundInToken
)
from app.models.user import User
from app.repositories.user import UserRepository

class AuthService:
  def __init__(self, repo: UserRepository):
    self.repo = repo

  # =======================
  # Локальна авторизація
  # =======================
  async def login(
    self, 
    email: str, 
    password: str
  ) -> dict:
    user: User = await self.repo.get_user_by_email(email)
    if not user or user.provider != "local":
      raise InvalidCredentials()
    if not user.hashed_password:
      raise InvalidCredentials("Password login not available for this account")
    if not verify_password(password, user.hashed_password):
      raise InvalidCredentials()
    if not user.is_active:
      raise UserDisabled()
    access_token = create_access_token({"sub": str(user.id), "email": user.email, "type": "access"})
    refresh_token = create_refresh_token({"sub": str(user.id), "type": "refresh"})
    return {
      "access_token": access_token, 
      "refresh_token": refresh_token, 
      "token_type": "bearer"
    }

  # =======================
  # Рефреш токен для авторизації
  # =======================
  async def refresh_access_token(
    self, 
    refresh_token: str
  ) -> dict:
    try:
      payload = decode_token(refresh_token)
    except Exception:
      raise InvalidToken()
    if payload.get("type") != "refresh":
      raise InvalidTokenType()
    user_id = payload.get("sub")
    if not user_id:
      raise InvalidTokenPayload()
    user: User = await self.repo.get_user_by_id(UUID(user_id))
    if not user:
      raise UserNotFound()
    if not user.is_active:
      raise UserDisabled()
    new_access_token = create_access_token({"sub": str(user.id), "email": user.email, "type": "access"})
    return {
      "access_token": new_access_token, 
      "token_type": "bearer"
    }

  # =======================
  # Поточний користувач із токена
  # =======================
  async def get_current_user_from_token(
    self, 
    token: str
  ) -> User:
    try:
      payload = decode_token(token)
    except Exception:
      raise InvalidToken()
    if payload.get("type") != "access":
      raise InvalidTokenType()
    user_id = payload.get("sub")
    if not user_id:
      raise InvalidTokenPayload()
    user: User = await self.repo.get_user_by_id(UUID(user_id))
    if not user:
      raise UserNotFound()
    if not user.is_active:
      raise UserDisabled()
    return user

  # =======================
  # Auth0 callback для даних із сервісу auth0
  # =======================
  async def handle_auth0_callback(
    self, 
    id_token: str
  ) -> dict:
    if not id_token:
      raise MissingIdToken()
    try:
      auth0_payload = decode_auth0_token(id_token)
    except Exception:
      raise InvalidAuth0Token()
    email = auth0_payload.get("email")
    provider_id = auth0_payload.get("sub")
    email_verified = auth0_payload.get("email_verified")
    if not email:
      raise EmailNotFoundInToken()
    if not email_verified:
      raise EmailNotVerified()
    # Шукаємо користувача за provider_id або email
    user: User = await self.repo.get_user_by_provider_id(provider_id)
    if not user:
      user = await self.repo.get_user_by_email(email)
    # Створюємо нового користувача, якщо його немає
    if not user:
      user_model = User(
        email=email,
        username=email.split("@")[0],
        hashed_password=None,  # сервіс auth0 паролю немає
        provider="auth0",
        provider_id=provider_id,
      )
    user = await self.repo.create_user(user_model)
    access_token = create_access_token({"sub": str(user.id), "email": user.email})
    refresh_token = create_refresh_token({"sub": str(user.id)})
    return {
      "access_token": access_token, 
      "refresh_token": refresh_token, 
      "token_type": "bearer"
    }
