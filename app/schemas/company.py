from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import List

from app.schemas.user import UserSchema

class CompanySchema(BaseModel):
  """Схема для читання компанії (відповідь API)"""
  id: UUID
  owner_id: UUID
  name: str
  description: str | None = None
  is_visible: bool
  created_at: datetime
  updated_at: datetime
  model_config = ConfigDict(from_attributes=True)

class CompanyCreateRequest(BaseModel):
  """Схема для створення компанії"""
  name: str = Field(min_length=1, max_length=255)
  description: str | None = None
  is_visible: bool = True

class CompanyUpdateRequest(BaseModel):
  """Схема для оновлення компанії"""
  model_config = ConfigDict(extra="forbid")
  name: str | None = Field(default=None, min_length=1, max_length=255)
  description: str | None = None
  is_visible: bool = True

class CompaniesListResponse(BaseModel):
  """Відповідь API зі списком компаній"""
  companies: List[CompanySchema]
  total: int

class CompanyDetailResponse(CompanySchema):
  """Детальна інформація про компанію"""
  pass

class CompanyWithOwnerSchema(BaseModel):
  id: UUID
  name: str
  description: str | None = None
  is_visible: bool
  created_at: datetime
  updated_at: datetime
  owner: UserSchema
  model_config = ConfigDict(from_attributes=True)
