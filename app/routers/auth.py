from uuid import UUID

from fastapi import APIRouter, Depends, Body
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from jose.exceptions import JWTError
from app.models.user import User
from app.schemas.user import SignInRequest, SignUpRequest
from app.services.user import UserService
from app.core.security import (
  verify_password,
  create_access_token,
  create_refresh_token,
  decode_token
)
from app.core.dependencies import get_current_user
from app.db.postgres import get_db
from app.core.auth0 import decode_auth0_token
from app.config import settings
from app.core.exceptions import (
  InvalidCredentials,
  InvalidToken,
  InvalidTokenType,
  InvalidTokenPayload,
  UserNotFound,
  UserDisabled,
  AuthProviderUnknown,
  MissingIdToken,
  InvalidAuth0Token,
  EmailNotVerified,
  EmailNotFoundInToken,
)

router = APIRouter(tags=["auth"])
security = HTTPBearer()

@router.post("/login")
async def login(
  data: SignInRequest,
  db: AsyncSession = Depends(get_db)
):
  user_service = UserService(db)
  user = await user_service.get_user_by_email(data.email)
  if not user or user.provider != "local":
    raise InvalidCredentials()
  if not user.hashed_password:
    raise InvalidCredentials("Password login not available for this account")
  if not verify_password(data.password, user.hashed_password):
    raise InvalidCredentials()
  if not user.is_active:
    raise UserDisabled()
  access_token = create_access_token({
    "sub": str(user.id),
    "email": user.email,
    "type": "access"
  })
  refresh_token = create_refresh_token({
    "sub": str(user.id),
    "type": "refresh"
  })
  return {
    "access_token": access_token,
    "refresh_token": refresh_token,
    "token_type": "bearer"
  }

@router.post("/logout")
async def logout(
  current_user: User = Depends(get_current_user)
):
  """
  Універсальний логаут:
  - Для локальних користувачів: можна видалити refresh token з БД (якщо зберігається)
  - Для Auth0: редірект на Auth0 logout URL
  """
  # Якщо користувач локальний — можна додати логіку видалення/інвалідації refresh token
  if current_user.provider == "local":
    # Наприклад, очищаємо refresh token в БД
    # await user_service.clear_refresh_token(current_user.id)
    return JSONResponse({"message": "Logged out successfully (local user)"})
  # Для Auth0 редірект на logout URL
  elif current_user.provider == "auth0":
    logout_url = (
      f"https://{settings.auth0_domain}/v2/logout?"
      f"client_id={settings.auth0_client_id}&returnTo={settings.frontend_redirect_url}"
    )
    return RedirectResponse(url=logout_url)
  else:
    raise AuthProviderUnknown("Unknown provider, cannot logout")

@router.post("/refresh")
async def refresh_token(
  credentials: HTTPAuthorizationCredentials = Depends(security),
  db: AsyncSession = Depends(get_db)
):
  """
  Приймає refresh token і повертає новий access token.
  Токен передається у Authorization: Bearer <refresh_token>
  """
  token = credentials.credentials
  try:
    payload = decode_token(token)
  except Exception:
    raise InvalidToken()
  if payload.get("type") != "refresh":
    raise InvalidTokenType()
  user_id = payload.get("sub")
  if not user_id:
    raise InvalidTokenPayload()
  user_service = UserService(db)
  user = await user_service.get_user_by_id(UUID(user_id))
  if not user:
    raise UserNotFound()
  if not user.is_active:
    raise UserDisabled()
  access_token = create_access_token({
    "sub": str(user.id),
    "email": user.email,
    "type": "access"
  })
  return {
    "access_token": access_token,
    "token_type": "bearer"
  }

@router.post("/callback")
async def auth0_callback(
  data: dict = Body(...),
  db: AsyncSession = Depends(get_db)
):
  """
  Frontend передає нам JSON з токенами від Auth0 після успішної авторизації користувача.:
  {
    "access_token": "...",
    "id_token": "...",
    "scope": "openid profile email",
    "expires_in": 86400,
    "token_type": "Bearer"
  }
  """
  """
    Далі, ми отримуємо JSON від фронтенду з access_token/id_token.
    Декодуємо id_token → беремо email + sub.
    Створюємо або знаходимо користувача в локальній БД.
    Видаємо локальний JWT і редіректимо на фронтенд.
  """
  print(data)  # Дебаг для перевірки отриманих даних від фронтенду
  id_token = data.get("id_token")
  if not id_token:
    raise MissingIdToken()
  # Декодуємо Auth0 token після верифікації сигнатури і отримуємо payload з email
  try:
    auth0_payload = decode_auth0_token(id_token)
  except JWTError:
    raise InvalidAuth0Token()
  email = auth0_payload.get("email")
  provider_id = auth0_payload.get("sub")
  email_verified = auth0_payload.get("email_verified")
  if not email:
    raise EmailNotFoundInToken()
  if not email_verified:
    raise EmailNotVerified()
  print(email)  # Дебаг для перевірки отриманого email з token_id
  # Шукаємо користувача: спочатку за provider_id, потім за email
  user_service = UserService(db)
  user = await user_service.get_user_by_provider_id(provider_id)
  if not user:
    user = await user_service.get_user_by_email(email)
  if not user:
    user = await user_service.create_new_user(
    SignUpRequest(
      email=email,
      username=email.split("@")[0],
      password=None,
      provider="auth0",
      provider_id=provider_id
    )
  )
  # Створюємо локальний JWT
  local_access_token = create_access_token({
    "sub": str(user.id),
    "email": user.email
  })
  local_refresh_token = create_refresh_token({
    "sub": str(user.id)
  })
  return {
    "access_token": local_access_token,
    "refresh_token": local_refresh_token,
    "token_type": "bearer"
  }
