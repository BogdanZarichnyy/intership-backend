from uuid import UUID
from pydantic import BaseModel, ConfigDict
from datetime import datetime

class NotificationSchema(BaseModel):
  id: UUID
  user_id: UUID
  quiz_id: UUID
  message: str
  is_read: bool
  created_at: datetime

  model_config = ConfigDict(from_attributes=True)
