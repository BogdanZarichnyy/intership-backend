from uuid import UUID
from pydantic import BaseModel, EmailStr, ConfigDict
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

  model_config = ConfigDict(from_attributes=True)

class SignInRequest(BaseModel):
  """Схема для входу користувача"""
  email: EmailStr
  password: str

class SignUpRequest(BaseModel):
  """Схема для реєстрації користувача"""
  email: EmailStr
  username: str
  password: str | None = None  # тепер дозволяємо None для авторизованих користувачів через сервіс auth0
  provider: str | None = None
  provider_id: str | None = None

class UserUpdate(BaseModel):
  """Схема для оновлення користувача"""
  model_config = ConfigDict(extra="forbid")
  username: str | None = None
  current_password: str | None = None  # поточний пароль для підтвердження
  new_password: str | None = None      # новий пароль, який користувач хоче встановити

class UsersListResponse(BaseModel):
  """Відповідь API зі списком користувачів"""
  users: list[UserSchema]
  total: int

class UserDetailResponse(UserSchema):
  """Відповідь API з детальною інформацією про користувача з ролями та компаніями"""
  # Список компаній, де користувач є власником
  owned_company_ids: list[UUID] = []
  # Список компаній, де користувач є учасником
  member_company_ids: list[UUID] = []

  def is_owner_of_company(self, company_id: UUID) -> bool:
    return company_id in self.owned_company_ids

  def is_member_of_company(self, company_id: UUID) -> bool:
    return company_id in self.member_company_ids
