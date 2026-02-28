from uuid import UUID
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token
from app.core.auth0 import decode_auth0_token
from app.services.user import UserService
from app.db.postgres import get_db
from app.repositories.user import UserRepository

from app.core.log_context import current_user_id_var

security = HTTPBearer()

def get_user_service(
  db: AsyncSession = Depends(get_db)
) -> UserService:
  return UserService(UserRepository(db))

async def get_current_user(
  credentials: HTTPAuthorizationCredentials = Depends(security),
  db: AsyncSession = Depends(get_user_service)
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
    user = await user_service.get_user_by_id(UUID(user_id))
    if not user:
      raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="User not found"
    )
    current_user_id_var.set(str(user.id))  # ← додаємо це для логування
    return user
  # Якщо локальний JWT не пройшов, пробуємо Auth0
  except Exception:
    try:
      payload = decode_auth0_token(token)
    except Exception:
      raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid token"
      )
    # Шукаємо користувача спочатку по provider_id, потім по email
    provider_id = payload.get("sub")  # унікальний ID від Auth0
    email = payload.get("email")
    user = await user_service.get_user_by_provider_id(provider_id)
    if not user:
      user = await user_service.get_user_by_email(email)
    if not email:
      raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Token missing email claim"
      )
    current_user_id_var.set(str(user.id))  # ← додаємо це для логування
    return user
