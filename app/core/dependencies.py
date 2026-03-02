from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.auth import AuthService
from app.repositories.user import UserRepository
from app.services.user import UserService
from app.db.postgres import get_db
from app.core.log_context import current_user_id_var

security = HTTPBearer()

# =========================
# UserService dependency
# =========================
def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
  return UserService(UserRepository(db))

# =========================
# AuthService dependency
# =========================
def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
  return AuthService(UserRepository(db))

# =========================
# Поточний користувач із токена
# =========================
async def get_current_user(
  credentials: HTTPAuthorizationCredentials = Depends(security),
  service: AuthService = Depends(get_auth_service),
):
  user = await service.get_current_user_from_token(credentials.credentials)
  current_user_id_var.set(str(user.id))  # ← додаємо це для логування, щоб бачити хто авторизований
  return user
