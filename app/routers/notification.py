from uuid import UUID
from fastapi import APIRouter, Depends, status
from app.core.dependencies import get_current_user, get_notification_service
from app.models.user import User
from app.schemas.notification import NotificationSchema
from app.services.notification import NotificationService

router = APIRouter(tags=["Notifications"])

@router.get(
  "/company/{company_id}/me", 
  status_code=status.HTTP_200_OK,
  response_model=list[NotificationSchema]
)
async def list_notifications(
  company_id: UUID, 
  current_user: User = Depends(get_current_user), 
  service: NotificationService = Depends(get_notification_service)
) -> list[NotificationSchema]:
  return await service.get_notifications_for_user(company_id, current_user)

@router.patch(
  "/mark/{notification_id}/as-read",
  status_code=status.HTTP_200_OK,
  response_model=NotificationSchema
)
async def mark_notification(
  notification_id: UUID, 
  current_user: User = Depends(get_current_user), 
  service: NotificationService = Depends(get_notification_service)
) -> NotificationSchema:
  return await service.mark_notification_as_read(notification_id, current_user)
