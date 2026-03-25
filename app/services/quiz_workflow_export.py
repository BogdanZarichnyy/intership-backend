from uuid import UUID
from app.core.logger import logger
from app.core.exceptions import QuizExportNotFound, CompanyNotFound, CompanyOwnerOnly
from app.models.user import User
from app.repositories.company import CompanyRepository
from app.repositories.company_member import CompanyMemberRepository
from app.services.company_member import CompanyMemberService
from app.services.quiz_workflow_redis_cache import QuizAttemptCacheService

class QuizExportService:
  def __init__(
    self,
    member_repo: CompanyMemberRepository,
    company_repo: CompanyRepository,
    company_member_service: CompanyMemberService,
    redis_cache: QuizAttemptCacheService
  ):
    self.member_repo = member_repo
    self.company_repo = company_repo
    self.company_member_service = company_member_service
    self.redis_cache = redis_cache

  # =====================================
  # Отримати власний quiz
  # =====================================
  async def get_my_quiz_workflow_attempts(
    self,
    current_user: User,
  ) -> list[dict]:
    attempts = await self.redis_cache.get_user_attempts(current_user.id)
    if not attempts:
      raise QuizExportNotFound()
    return attempts

  # =====================================
  # Отримати quiz конкретного користувача
  # =====================================
  async def get_company_member_quiz_workflow_attempts(
    self,
    company_id: UUID,
    current_user: User,
    user_id: UUID | None = None,
  ) -> list[dict]:
    await self.company_member_service.check_owner_or_admin(company_id, current_user.id)
    company = await self.company_repo.get_company_by_id(company_id)
    if not company:
      logger.warning(f"Company {company_id} not found during owner/admin check")
      raise CompanyNotFound()
    member = await self.member_repo.get_member_of_company(company_id, user_id)
    if not member:
      logger.info(f"User {current_user.id} is not member of company {company_id}")
      raise CompanyOwnerOnly()
    attempts = await self.redis_cache.get_company_user_attempts(company_id, user_id)
    if not attempts:
      raise QuizExportNotFound()
    return attempts

  # ====================================
  # Отримати всі quizzes членів компанії
  # ====================================
  async def get_company_members_quiz_workflow_attempts(
    self,
    company_id: UUID,
    current_user: User,
  ) -> list[dict]:
    logger.info(f"User {current_user.id} requesting all users' attempts for company {company_id}") 
    await self.company_member_service.check_owner_or_admin(company_id, current_user.id)
    company = await self.company_repo.get_company_by_id(company_id)
    if not company:
      logger.warning(f"Company {company_id} not found during owner/admin check")
      raise CompanyNotFound()
    attempts = await self.redis_cache.get_company_attempts(company_id)
    if not attempts:
      raise QuizExportNotFound()
    return attempts

  # ============================================================
  # Отримати результати конкретного quiz по всіх членах компанії
  # ============================================================
  async def get_company_quiz_workflow_attempts(
    self,
    company_id: UUID,
    quiz_id: UUID,
    current_user: User,
  ) -> list[dict]:
    logger.info(f"User {current_user.id} requesting attempts for quiz {quiz_id}")
    await self.company_member_service.check_owner_or_admin(company_id, current_user.id)
    company = await self.company_repo.get_company_by_id(company_id)
    if not company:
      logger.warning(f"Company {company_id} not found during owner/admin check")
      raise CompanyNotFound()
    attempts = await self.redis_cache.get_quiz_attempts(company_id, quiz_id)
    if not attempts:
      raise QuizExportNotFound()
    return attempts
