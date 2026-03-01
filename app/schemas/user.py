from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from datetime import datetime

class UserSchema(BaseModel):
  """Схема для читання користувача (відповідь API)"""
  id: UUID
  email: EmailStr
  username: str
  provider: str
  provider_id: str | None = None
  is_active: bool
  created_at: datetime
  updated_at: datetime

  class Config:
    from_attributes = True  # Для SQLAlchemy об'єктів

class SignInRequest(BaseModel):
  """Схема для входу користувача"""
  email: EmailStr
  password: str

class SignUpRequest(BaseModel):
  """Схема для реєстрації користувача"""
  email: EmailStr
  username: str
  password: str
  provider: str | None = None
  provider_id: str | None = None

class UserUpdate(BaseModel):
  """Схема для оновлення користувача"""
  model_config = ConfigDict(extra="forbid")
  username: str | None = None
  current_password: str | None = None  # поточний пароль для підтвердження
  new_password: str | None = None     # новий пароль, який користувач хоче встановити

class UsersListResponse(BaseModel):
  """Відповідь API зі списком користувачів"""
  users: list[UserSchema]
  total: int

class UserDetailResponse(UserSchema):
  """Відповідь API з детальною інформацією про користувача з ролями та компаніями"""
  pass
