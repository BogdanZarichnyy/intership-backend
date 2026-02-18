from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
import httpx

from app.schemas.user import SignInRequest
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

router = APIRouter(tags=["auth"])
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
    # f"https://{settings.auth0_domain}/v2/logout?"
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
  OAuth2 callback:
  1. Отримуємо code від Auth0
  2. Обмінюємо його на токени через /oauth/token
  3. Беремо id_token → дістаємо email
  4. Створюємо/знаходимо користувача
  5. Видаємо локальний JWT і редіректимо на фронтенд
  """

  print(request.query_params)  # Дебаг для перевірки отриманих параметрів
  print(request.query_params.get("code"))  # Дебаг для перевірки отримання коду авторизації
  print(request.query_params.get("state"))  # Дебаг для перевірки отримання state параметра
  print(request.query_params.get("token"))  # Дебаг для перевірки отримання state параметра

  code = request.query_params.get("code")
  if not code:
    raise HTTPException(status_code=400, detail="Missing code from Auth0")
  token_url = f"https://{settings.auth0_domain}/oauth/token"
  payload = {
    "grant_type": "authorization_code",
    "client_id": settings.auth0_client_id,
    "client_secret": settings.auth0_client_secret,
    "code": code,
    "redirect_uri": settings.auth0_redirect_uri,
  }
  async with httpx.AsyncClient() as client:
    response = await client.post(token_url, json=payload)
  if response.status_code != 200:
    raise HTTPException(
      status_code=response.status_code,
      detail=f"Auth0 token exchange failed: {response.text}"
    )
  token_data = response.json()
  id_token = token_data.get("id_token")
  if not id_token:
    raise HTTPException(status_code=400, detail="id_token not returned by Auth0")
  auth0_payload = decode_auth0_token(id_token)
  email = auth0_payload.get("email")
  if not email:
    raise HTTPException(status_code=400, detail="Email not found in id_token")
  user_service = UserService(db)
  user = await user_service.get_user_by_email(email)
  if not user:
    user = await user_service.create_new_user({
      "email": email,
      "username": email.split("@")[0],
      "password": None
    })
  local_access_token = create_access_token({
    "sub": str(user.id),
    "email": user.email
  })
  redirect_url = f"{settings.auth0_redirect_uri}?access_token={local_access_token}"
  return RedirectResponse(url=redirect_url)