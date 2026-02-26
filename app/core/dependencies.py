from uuid import UUID
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token
from app.core.auth0 import decode_auth0_token
from app.services.company_invitation import CompanyInvitationService
from app.services.user import UserService
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
    user = await user_service.get_user_by_id(UUID(user_id))
    if not user:
      raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="User not found"
    )
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
    return user

def get_invitation_service(
  db: AsyncSession = Depends(get_db)
):
  return CompanyInvitationService(db)
