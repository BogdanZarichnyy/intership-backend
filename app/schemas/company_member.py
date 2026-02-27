from uuid import UUID
from datetime import datetime
from pydantic import BaseModel
from app.models.company_member import CompanyRole

class CompanyMemberBase(BaseModel):
  company_id: UUID
  member_id: UUID

class CompanyMemberCreate(CompanyMemberBase):
  role: CompanyRole = CompanyRole.member  # За замовчуванням 'member'

class CompanyMemberResponse(CompanyMemberBase):
  role: CompanyRole
  created_at: datetime
  updated_at: datetime

  class Config:
    from_attributes = True

class CompanyAdminsResponse(BaseModel):
  admins: list[CompanyMemberResponse]

  class Config:
    from_attributes = True
