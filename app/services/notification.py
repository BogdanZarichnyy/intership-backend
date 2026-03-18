from uuid import UUID
from app.core.logger import logger
from app.core.exceptions import NotificationNotFound, NotificationForbidden, CompanyNotFound, CompanyMembershipForbidden
from app.models.user import User
from app.repositories.company import CompanyRepository
from app.repositories.company_member import CompanyMemberRepository
from app.repositories.notification import NotificationRepository
from app.schemas.notification import NotificationSchema

class NotificationService:
  def __init__(self, notification_repo: NotificationRepository, company_repo: CompanyRepository, member_repo: CompanyMemberRepository):
    self.company_repo = company_repo
    self.member_repo = member_repo
    self.notification_repo = notification_repo

  # Створює сповіщення для всіх членів компанії
  async def create_notification_quiz(
    self, 
    company_id: UUID, 
    quiz_id: UUID, 
    message: str,
  ):
    # Отримуємо всіх членів компанії
    members = await self.member_repo.get_all_members_for_notifications(company_id)
    if not members:
      logger.warning(f"No members found in company {company_id} for quiz notification")
      return
    notifications_data = [
      {
        "user_id": member.member_id,
        "quiz_id": quiz_id,
        "message": message,
      }
      for member in members
    ]
    # Використовуємо батчеву вставку з NotificationRepository
    await self.notification_repo.create_notifications_bulk(notifications_data)
    logger.info(f"Created {len(notifications_data)} notifications for quiz {quiz_id} in company {company_id}")

  # Отримати список сповіщень користувача
  async def get_notifications_for_user(
    self, 
    company_id: UUID,
    current_user: User
  ) -> list[NotificationSchema]:
    company = await self.company_repo.get_company_by_id(company_id)
    if not company:
      logger.warning(f"Company not found company_id={company_id}")
      raise CompanyNotFound()
    # Перевіряємо, чи користувач являється членом компанії
    member = await self.member_repo.get_member_of_company(company_id, current_user.id)
    # Якщо не член, перевіряємо чи власник
    if not member:
      logger.warning(f"User {current_user.id} is not member of company {company_id}")
      raise CompanyMembershipForbidden("User must be a company member to view this notifications")
    logger.info(f"Fetching notifications for user {current_user.id}")
    notifications = await self.notification_repo.get_user_notifications(current_user.id)
    return [
      NotificationSchema.model_validate(notification)
      for notification in notifications
    ]
  
  # Позначити сповіщення як прочитане
  async def mark_notification_as_read(
    self, 
    notification_id: UUID, 
    current_user: User
  ):
    # Перевірка, чи існує сповіщення
    notification = await self.notification_repo.get_notification_by_id(notification_id)
    if not notification:
      logger.warning(f"Notification {notification_id} not found for user {current_user.id}")
      raise NotificationNotFound()
    # Перевірка прав: користувач може змінювати тільки власні сповіщення
    if notification.user_id != current_user.id:
      logger.warning(f"User {current_user.id} tried to mark notification {notification_id} not belonging to them")
      raise NotificationForbidden()
    notification = await self.notification_repo.mark_notification_as_read(notification_id, current_user.id)
    logger.info(f"User {current_user.id} marked notification {notification_id} as read")
    return NotificationSchema.model_validate(notification)
