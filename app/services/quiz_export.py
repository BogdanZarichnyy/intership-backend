from uuid import UUID
from app.core.logger import logger
from app.core.exceptions import QuizExportNotFound
from app.db.redis import redis_client
from app.models.user import User
from app.repositories.company_member import CompanyMemberRepository
from app.services.quiz import QuizService
from app.utils.export_from_redis import scan_attempts

class QuizExportService:
  def __init__(
    self,
    quiz_service: QuizService,
    member_repo: CompanyMemberRepository,
  ):
    self.quiz_service = quiz_service
    self.member_repo = member_repo
    self.redis = redis_client

  async def _filter_attempts_by_company(
    self, 
    attempts: list[dict], 
    company_id: UUID
  ) -> list[dict]:
    filtered = [a for a in attempts if a.get("company_id") == str(company_id)]
    logger.info(f"Filtered {len(filtered)}/{len(attempts)} attempts for company {company_id}")
    if not filtered:
      logger.warning(f"No attempts found for company {company_id}")
      raise QuizExportNotFound()
    return filtered

  async def get_user_attempts(
    self,
    company_id: UUID,
    current_user: User,
    user_id: UUID | None = None,
  ) -> list[dict]:
    if user_id and user_id != current_user.id:
      logger.info(f"User {current_user.id} requesting attempts for user {user_id}")
      await self.quiz_service.check_owner_or_admin(company_id, current_user.id)
    else:
      user_id = current_user.id
    pattern = f"quiz_attempt:{user_id}:*"
    logger.info(f"Scanning Redis for pattern '{pattern}'")
    attempts = await scan_attempts(self.redis, pattern)
    logger.info(f"Found {len(attempts)} attempts in Redis for user {user_id}")
    return await self._filter_attempts_by_company(attempts, company_id)

  async def get_users_attempts(
    self,
    company_id: UUID,
    current_user: User,
  ) -> list[dict]:
    logger.info(f"User {current_user.id} requesting all users' attempts for company {company_id}") 
    await self.quiz_service.check_owner_or_admin(company_id, current_user.id)
    attempts = await scan_attempts(self.redis, "quiz_attempt:*")
    return await self._filter_attempts_by_company(attempts, company_id)

  async def get_quiz_attempts(
    self,
    company_id: UUID,
    quiz_id: UUID,
    current_user: User,
  ) -> list[dict]:
    logger.info(f"User {current_user.id} requesting attempts for quiz {quiz_id}")
    await self.quiz_service.check_owner_or_admin(company_id, current_user.id)
    pattern = f"quiz_attempt:*:{quiz_id}"
    logger.info(f"Scanning Redis for pattern '{pattern}'")
    attempts = await scan_attempts(self.redis, pattern)
    logger.info(f"Found {len(attempts)} attempts in Redis for quiz {quiz_id}")
    return await self._filter_attempts_by_company(attempts, company_id)
