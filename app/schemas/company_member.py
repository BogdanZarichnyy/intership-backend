from uuid import UUID
from pydantic import BaseModel, ConfigDict
from datetime import datetime

class CompanyMemberBase(BaseModel):
  company_id: UUID
  member_id: UUID

class CompanyMemberResponse(CompanyMemberBase):
  created_at: datetime

  model_config = ConfigDict(from_attributes=True)

class CompanyAdminsResponse(BaseModel):
  admins: list[CompanyMemberResponse]

  model_config = ConfigDict(from_attributes=True)
