from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict

from app.models.company_invitation import InvitationStatus

class InvitationResponse(BaseModel):
  id: UUID
  company_id: UUID
  invited_user_id: UUID
  invited_by: UUID
  status: InvitationStatus
  created_at: datetime
  updated_at: datetime

  model_config = ConfigDict(from_attributes=True)
