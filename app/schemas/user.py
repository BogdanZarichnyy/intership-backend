from uuid import UUID
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import List

class UserSchema(BaseModel):
  """Схема для читання користувача (відповідь API)"""
  id: UUID
  email: EmailStr
  username: str
  is_active: bool
  created_at: datetime
  updated_at: datetime

  class Config:
    from_attributes = True  # Для SQLAlchemy об'єктів

class SignInRequest(BaseModel):
  """Модель запиту для входу користувача"""
  email: EmailStr
  password: str

class SignUpRequest(BaseModel):
  """Модель запиту для реєстрації користувача"""
  email: EmailStr
  username: str = Field(min_length=3, max_length=100)
  password: str = Field(min_length=6)

class UserUpdate(BaseModel):
  """Схема для оновлення користувача (CRUD)"""
  email: EmailStr | None = None
  username: str | None = None
  password: str | None = None
  is_active: str | None = None

class UsersListResponse(BaseModel):
  """Відповідь API зі списком користувачів"""
  users: List[UserSchema]
  total: int

class UserDetailResponse(UserSchema):
  """Відповідь API з детальною інформацією про користувача"""
  pass
