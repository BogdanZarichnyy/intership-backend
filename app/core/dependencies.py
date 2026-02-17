from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token
from app.core.auth0 import decode_auth0_token  # новий модуль
from app.services.user import UserService
from app.schemas.user import SignUpRequest
from app.db.postgres import get_db

security = HTTPBearer()

async def get_current_user(
  credentials: HTTPAuthorizationCredentials = Depends(security),
  db: AsyncSession = Depends(get_db)
):
  token = credentials.credentials
  user_service = UserService(db)
  # Пробуємо локальний JWT
  try:
    payload = decode_token(token)
    if payload.get("type") != "access":
      raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid token type"
      )
    user_id = payload.get("sub")
    user = await user_service.get_user_by_id(int(user_id))
    if not user:
      raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="User not found"
    )
    return user
  except Exception:
    # Якщо локальний JWT не пройшов, пробуємо Auth0
    try:
      payload = decode_auth0_token(token)
    except Exception:
      raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid token"
      )
    email = payload.get("email")
    if not email:
      raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Token missing email claim"
      )
    user = await user_service.get_user_by_email(email)
    if not user:
      # Динамічно створюємо користувача у базі
      user = await user_service.create_new_user(
        SignUpRequest(email=email, username=email.split("@")[0], password=None)
      )
    return user