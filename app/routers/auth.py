from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.user import SignInRequest, SignUpRequest
from app.services.user import UserService
from app.core.security import (
  verify_password,
  create_access_token,
  create_refresh_token,
  decode_token
)
from app.db.postgres import get_db
from app.core.auth0 import decode_auth0_token
from app.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBearer()

@router.post("/login")
async def login(
  data: SignInRequest,
  db: AsyncSession = Depends(get_db)
):
  user_service = UserService(db)
  user = await user_service.get_user_by_email(data.email)
  if not user or not verify_password(data.password, user.hashed_password):
    raise HTTPException(
      status_code=status.HTTP_401_UNAUTHORIZED,
      detail="Invalid credentials"
    )
  access_token = create_access_token({
    "sub": str(user.id),
    "email": user.email
  })
  refresh_token = create_refresh_token({
    "sub": str(user.id)
  })
  return {
    "access_token": access_token,
    "refresh_token": refresh_token,
    "token_type": "bearer"
  }

@router.get("/logout")
async def auth0_logout():
  """
  Логаут користувача на Auth0.
  Редірект на Auth0 logout URL і повернення на фронтенд.
  """
  logout_url = (
    f"https://{settings.auth0_domain}/v2/logout?"
    f"client_id={settings.auth0_client_id}&returnTo={settings.auth0_redirect_uri}"
  )
  return RedirectResponse(url=logout_url)

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
    raise HTTPException(
      status_code=status.HTTP_401_UNAUTHORIZED,
      detail="Invalid token"
    )
  if payload.get("type") != "refresh":
    raise HTTPException(
      status_code=status.HTTP_401_UNAUTHORIZED,
      detail="Invalid token type"
    )
  user_service = UserService(db)
  user_id = payload.get("sub")
  user = await user_service.get_user_by_id(int(user_id))
  if not user:
    raise HTTPException(
      status_code=status.HTTP_404_NOT_FOUND,
      detail="User not found"
    )
  access_token = create_access_token({
    "sub": str(user.id),
    "email": user.email
  })
  return {
    "access_token": access_token,
    "token_type": "bearer"
  }

@router.get("/callback")
async def auth0_callback(request: Request, db: AsyncSession = Depends(get_db)):
  """
  Обробляє редірект після логіну через Auth0.
  Отримує token як query параметр, створює користувача у БД, якщо його немає,
  і видає локальний access_token для бекенду.
  """
  print(request.query_params)  # Дебаг для перевірки отриманих параметрів
  token = request.query_params.get("token")
  if not token:
    raise HTTPException(status_code=400, detail="Token not provided by Auth0")
  try:
    payload = decode_auth0_token(token)
  except Exception as e:
    raise HTTPException(status_code=401, detail=f"Invalid Auth0 token: {str(e)}")
  email = payload.get("email")
  if not email:
    raise HTTPException(status_code=400, detail="Auth0 token does not contain email")
  user_service = UserService(db)
  user = await user_service.get_user_by_email(email)
  if not user:
    # Динамічне створення користувача
    user = await user_service.create_new_user(
      user_data={
        "email": email,
        "username": email.split("@")[0],
        "password": None  # пароль не потрібен для Auth0 користувачів
      }
    )
  # Створюємо локальний access_token для бекенду
  access_token = create_access_token({"sub": str(user.id), "email": user.email})
  # Редіректимо на фронтенд SPA, передаємо токен у query параметрі
  redirect_url = f"${settings.auth0_redirect_uri}?access_token={access_token}"
  return RedirectResponse(url=redirect_url)
