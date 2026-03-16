from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime

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
  name: str | None = Field(default=None, min_length=1, max_length=255)
  description: str | None = None
  is_visible: bool | None = None

  model_config = ConfigDict(extra="forbid")

  model_config = ConfigDict(extra="forbid")

  model_config = ConfigDict(extra="forbid")

  model_config = ConfigDict(extra="forbid")

class CompaniesListResponse(BaseModel):
  """Відповідь API зі списком компаній"""
  companies: list[CompanySchema]
  total: int
