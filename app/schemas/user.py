from uuid import UUID
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import List, Optional

class UserSchema(BaseModel):
  """Схема для читання користувача (відповідь API)"""
  id: UUID
  email: EmailStr
  username: str
  provider: str
  provider_id: Optional[str] = None
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
  username: str = Field(min_length=3, max_length=100)
  password: str = Field(min_length=6)
  provider: str | None = None
  provider_id: str | None = None

class UserUpdate(BaseModel):
  """Схема для оновлення користувача"""
  email: EmailStr | None = None
  username: str | None = None
  is_active: str | None = None
  current_password: str | None = None  # поточний пароль для підтвердження
  new_password: str | None = None     # новий пароль, який користувач хоче встановити

class UsersListResponse(BaseModel):
  """Відповідь API зі списком користувачів"""
  users: List[UserSchema]
  total: int

class UserDetailResponse(UserSchema):
  """Відповідь API з детальною інформацією про користувача"""
  pass
