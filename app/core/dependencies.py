from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.log_context import current_user_id_var
from app.db.postgres import get_db
from app.models.user import User
from app.repositories.user import UserRepository
from app.repositories.company import CompanyRepository
from app.repositories.company_member import CompanyMemberRepository
from app.repositories.company_invitation import CompanyInvitationRepository
from app.repositories.quiz import QuizRepository
from app.repositories.quiz_workflow import QuizWorkflowRepository
from app.repositories.analytics import AnalyticsRepository
from app.repositories.notification import NotificationRepository
from app.services.user import UserService
from app.services.auth import AuthService
from app.services.company import CompanyService
from app.services.company_member import CompanyMemberService
from app.services.company_invitation import CompanyInvitationService
from app.services.company_role import CompanyAdminService
from app.services.quiz import QuizService
from app.services.quiz_workflow import QuizWorkflowService
from app.services.quiz_workflow_redis_cache import QuizAttemptCacheService
from app.services.quiz_workflow_export import QuizExportService
from app.services.analytics import AnalyticsService
from app.services.notification import NotificationService
from app.services.notification_scheduler import QuizReminderService

security = HTTPBearer()

# UserService dependency
async def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
  return UserService(UserRepository(db))

# AuthService dependency
async def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
  return AuthService(UserRepository(db))

# Поточний користувач із токена
async def get_current_user(
  credentials: HTTPAuthorizationCredentials = Depends(security),
  service: AuthService = Depends(get_auth_service),
)-> User:
  user = await service.get_current_user_from_token(credentials.credentials)
  current_user_id_var.set(str(user.id))  # ← додаємо це для логування, щоб бачити хто авторизований
  return user

# CompanyService dependency
async def get_company_service(db: AsyncSession = Depends(get_db)) -> CompanyService:
  return CompanyService(CompanyRepository(db))

# CompanyMemberService dependency
async def get_company_member_service(db: AsyncSession = Depends(get_db)) -> CompanyMemberService:
  member_repo = CompanyMemberRepository(db)
  company_repo = CompanyRepository(db)
  return CompanyMemberService(member_repo, company_repo)

# CompanyInvitationService dependency
async def get_invitation_service(db: AsyncSession = Depends(get_db)) -> CompanyInvitationService:
  invitation_repo = CompanyInvitationRepository(db)
  member_repo = CompanyMemberRepository(db)
  company_repo = CompanyRepository(db)
  return CompanyInvitationService(invitation_repo, member_repo, company_repo)

# CompanyAdminService dependency
async def get_company_admin_service(db: AsyncSession = Depends(get_db)) -> CompanyAdminService:
  member_repo = CompanyMemberRepository(db)
  company_repo = CompanyRepository(db)
  return CompanyAdminService(member_repo, company_repo)

# NotificationService dependency
async def get_notification_service(db: AsyncSession = Depends(get_db)) -> NotificationService:
  notification_repo = NotificationRepository(db)
  company_repo = CompanyRepository(db)
  member_repo = CompanyMemberRepository(db)
  return NotificationService(notification_repo, company_repo, member_repo)

# QuizService dependency
async def get_quiz_service(
  db: AsyncSession = Depends(get_db),
  notification_service: NotificationService = Depends(get_notification_service)
) -> QuizService:
  quiz_repo = QuizRepository(db)
  quiz_workflow_repo = QuizWorkflowRepository(db)
  member_repo = CompanyMemberRepository(db)
  company_repo = CompanyRepository(db)
  company_member_service = CompanyMemberService(member_repo, company_repo)
  return QuizService(quiz_repo, quiz_workflow_repo, member_repo, company_repo, company_member_service, notification_service)

# QuizWorkflowCashRedisService dependency
def get_quiz_workflow_cache_redis_service() -> QuizAttemptCacheService:
  return QuizAttemptCacheService()

# QuizWorkflowService dependency
def get_quiz_workflow_service(
  db: AsyncSession = Depends(get_db),
  quiz_service: QuizService = Depends(get_quiz_service),
  company_member_service: CompanyMemberService = Depends(get_company_member_service),
  redis_cache: QuizAttemptCacheService = Depends(get_quiz_workflow_cache_redis_service)
) -> QuizWorkflowService:
  quiz_workflow_repo = QuizWorkflowRepository(db)
  member_repo = CompanyMemberRepository(db)
  return QuizWorkflowService(quiz_workflow_repo, member_repo, quiz_service, company_member_service, redis_cache)

# QuizExportService dependency
def get_quiz_export_service(
  db: AsyncSession = Depends(get_db), 
  company_member_service: CompanyMemberService = Depends(get_company_member_service),
  redis_cache: QuizAttemptCacheService = Depends(get_quiz_workflow_cache_redis_service)
) -> QuizExportService:
  quiz_repo = QuizRepository(db)
  member_repo = CompanyMemberRepository(db)
  company_repo = CompanyRepository(db)
  quiz_service = QuizService(
    quiz_repo=quiz_repo,
    member_repo=member_repo,
    company_repo=company_repo,
    company_member_service=company_member_service
  )
  return QuizExportService(
    quiz_service=quiz_service,
    company_member_service=company_member_service,
    redis_cache=redis_cache
  )

# AnalyticsService dependency
def get_analytics_service(
  db: AsyncSession = Depends(get_db),
  company_member_service: CompanyMemberService = Depends(get_company_member_service),
):
  repo = AnalyticsRepository(db)
  return AnalyticsService(repo, company_member_service)

# QuizReminderService dependency
async def get_quiz_reminder_service(
  db: AsyncSession = Depends(get_db)
) -> QuizReminderService:
  member_repo = CompanyMemberRepository(db)
  quiz_repo = QuizRepository(db)
  quiz_workflow_repo = QuizWorkflowRepository(db)
  notification_repo = NotificationRepository(db)
  return QuizReminderService(member_repo, quiz_repo, quiz_workflow_repo, notification_repo)
