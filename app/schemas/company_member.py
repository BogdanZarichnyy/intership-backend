from uuid import UUID
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from app.models.company_member import CompanyRole

class CompanyMemberBase(BaseModel):
  company_id: UUID
  member_id: UUID

class CompanyMemberResponse(CompanyMemberBase):
  role: CompanyRole
  created_at: datetime
  updated_at: datetime

  model_config = ConfigDict(from_attributes=True)

class CompanyAdminsResponse(BaseModel):
  admins: list[CompanyMemberResponse]

  model_config = ConfigDict(from_attributes=True)
