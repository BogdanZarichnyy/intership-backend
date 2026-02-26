from uuid import UUID
from pydantic import BaseModel
from datetime import datetime

class CompanyMemberBase(BaseModel):
  company_id: UUID
  member_id: UUID

class CompanyMemberCreate(CompanyMemberBase):
  pass  # Для додавання нового учасника

class CompanyMembersResponse(CompanyMemberBase):
  created_at: datetime

  class Config:
    from_attributes = True