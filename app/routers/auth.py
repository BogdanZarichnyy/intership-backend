from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Body
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
    raise HTTPException(
      status_code=status.HTTP_401_UNAUTHORIZED,
      detail="Invalid credentials"
    )
  if not user.hashed_password:
    raise HTTPException(
      status_code=status.HTTP_401_UNAUTHORIZED,
      detail="Password login not available for this account"
    )
  if not verify_password(data.password, user.hashed_password):
    raise HTTPException(
      status_code=status.HTTP_401_UNAUTHORIZED,
      detail="Invalid credentials"
    )
  if not user.is_active:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="User account is disabled"
    )
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
    raise HTTPException(
      status_code=status.HTTP_400_BAD_REQUEST,
      detail="Unknown provider, cannot logout"
    )

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
  user_id = payload.get("sub")
  if not user_id:
    raise HTTPException(
      status_code=status.HTTP_401_UNAUTHORIZED,
      detail="Invalid token payload"
    )
  user_service = UserService(db)
  user = await user_service.get_user_by_id(UUID(user_id))
  if not user:
    raise HTTPException(
      status_code=status.HTTP_404_NOT_FOUND,
      detail="User not found"
    )
  if not user.is_active:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="User account is disabled"
    )
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
      raise HTTPException(
          status_code=400,
          detail="Missing id_token"
      )
  # Декодуємо Auth0 token після верифікації сигнатури і отримуємо payload з email
  try:
    auth0_payload = decode_auth0_token(id_token)
  except JWTError:
    raise HTTPException(
      status_code=401,
      detail="Invalid Auth0 token"
    )
  email = auth0_payload.get("email")
  provider_id = auth0_payload.get("sub")
  email_verified = auth0_payload.get("email_verified")
  if not email:
    raise HTTPException(
      status_code=400,
      detail="Email not found in token"
    )
  if not email_verified:
    raise HTTPException(
      status_code=403,
      detail="Email not verified"
    )
  print(email)  # Дебаг для перевірки отриманого email з токена
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


# Я хотів би цей кусок коду залишити на майбутьнє і реалізувати отримання JWT токена спочатку на бекенд, 
# який потім передасть його з рефреш-токеном на фронтенд після усіх необхідних перевірок. 
# Такий механізм роботи передбачений сервісом 0auth для типу Regular Web Applications, де frontend 
# немає прямого доступу до секретів і токенів від провайдера, а весь процес авторизації і взаємодії 
# з провайдером відбувається на бекенді. Це більш безпечно, оскільки секрети і токени не потрапляють 
# на клієнтську сторону, а також дозволяє краще контролювати процес авторизації і обробки користувачів.


# @router.get("/callback")
# async def auth0_callback(request: Request, db: AsyncSession = Depends(get_db)):

#   """
#   OAuth2 callback:
#   1. Отримуємо code від Auth0
#   2. Обмінюємо його на токени через /oauth/token
#   3. Беремо id_token → дістаємо email
#   4. Створюємо/знаходимо користувача
#   5. Видаємо локальний JWT і редіректимо на фронтенд
#   """

#   print(request.query_params)  # Дебаг для перевірки отриманих параметрів
#   print(request.query_params.get("code"))  # Дебаг для перевірки отримання коду авторизації
#   print(request.query_params.get("state"))  # Дебаг для перевірки отримання state параметра

#   code = request.query_params.get("code")
#   if not code:
#     raise HTTPException(status_code=400, detail="Missing code from Auth0")
#   token_url = f"https://{settings.auth0_domain}/oauth/token"
#   payload = {
#     "grant_type": "authorization_code",
#     "client_id": settings.auth0_client_id,
#     "client_secret": settings.auth0_client_secret,
#     "code": code,
#     "redirect_uri": settings.auth0_redirect_uri,
#   }
#   headers = {
#     "Content-Type": "application/x-www-form-urlencoded"  # Auth0 вимагає саме цей Content-Type
#   }
#   async with httpx.AsyncClient() as client:
#     response = await client.post(token_url, data=payload, headers=headers)
#   if response.status_code != 200:
#     raise HTTPException(
#       status_code=response.status_code,
#       detail=f"Auth0 token exchange failed: {response.text}"
#     )
#   token_data = response.json()
#   print(token_data) # Дебаг для перевірки отриманих токенів від Auth0
#   id_token = token_data.get("id_token")
#   access_token = token_data.get("access_token")
#   if not id_token:
#     raise HTTPException(status_code=400, detail="id_token not returned by Auth0")
#   if not id_token or not access_token:
#     raise HTTPException(status_code=400, detail="Tokens not returned by Auth0")
#   auth0_payload = decode_auth0_token(id_token)
#   email = auth0_payload.get("email")
#   if not email:
#     raise HTTPException(status_code=400, detail="Email not found in id_token")
#   user_service = UserService(db)
#   user = await user_service.get_user_by_email(email)
#   if not user:
#     user = await user_service.create_new_user({
#       "email": email,
#       "username": email.split("@")[0],
#       "password": None
#     })
#   local_access_token = create_access_token({
#     "sub": str(user.id),
#     "email": user.email
#   })
#   # redirect to frontend
#   redirect_url = f"{settings.frontend_redirect_url}?access_token={local_access_token}"
#   return RedirectResponse(url=redirect_url)