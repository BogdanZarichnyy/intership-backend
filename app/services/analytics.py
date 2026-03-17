from datetime import datetime
from uuid import UUID
from app.core.exceptions import AnalyticsNotFound, AnalyticsForbidden, CompanyNotFound
from app.core.logger import logger
from app.models.user import User
from app.repositories.analytics import AnalyticsRepository
from app.services.company_member import CompanyMemberService
from app.schemas.analytics import (
  UserOverallRatingResponse, 
  UserQuizAverageScoreResponse, 
  UserQuizLastAttemptResponse, 
  CompanyMemberAverageScore,
  CompanyQuizAverageScore,
  QuizAverageScore,
  CompanyMemberLastAttempt,
  CompanyMemberLastAttemptsResponse
)
from app.utils.normalize_timestamps import normalize_timestamps

class AnalyticsService:
  def __init__(
    self,
    repo: AnalyticsRepository,
    company_member_service: CompanyMemberService
  ):
    self.repo = repo
    self.company_member_service = company_member_service

  # =============================
  # User analytics
  # =============================

  # Загальний рейтинг користувача - середній бал за всі квізи
  async def get_user_overall_rating_service(
    self, 
    current_user: User
  ) -> UserOverallRatingResponse:
    logger.info(f"Calculating overall score for user {current_user.id}")
    result = await self.repo.get_user_overall_rating_repo(current_user.id)
    if result is None:
      logger.warning(f"No analytics found for user_id={current_user.id}")
      raise AnalyticsNotFound("User analytics not found")
    return UserOverallRatingResponse.model_validate(result)

  # Список середніх балів для кожного квізу пройденого користувачем з часовими діапазонами
  async def get_user_average_scores_service(
    self, 
    current_user: User
  ) -> list[UserQuizAverageScoreResponse]:
    result = await self.repo.get_user_average_scores_repo(current_user.id)
    if not result:
      logger.warning(f"No quiz analytics found for user_id={current_user.id}")
      raise AnalyticsNotFound("User quiz analytics not found")
    logger.info(f"Fetching per-quiz scores for user {current_user.id}")
    return [
      UserQuizAverageScoreResponse.model_validate(row)
      for row in result
    ]

  # Список тестів разом з часовими позначками їх останнього виконання
  async def get_user_quiz_last_attempts(
    self, 
    current_user: User
  ) -> list[UserQuizLastAttemptResponse]:
    logger.info(f"Fetching last quizzes attempts for user {current_user.id}")
    result = await self.repo.get_user_quizzes_with_timestamps(current_user.id)
    if not result:
      logger.warning(f"No quiz analytics found for user_id={current_user.id}")
      raise AnalyticsNotFound("User quiz analytics not found")
    return [
      UserQuizLastAttemptResponse.model_validate(row)
      for row in result
    ]

  # =============================
  # Company analytics
  # =============================

  # Список середніх балів всіх членів компанії з часовими діапазонами
  async def get_company_members_scores(
    self, 
    company_id: UUID, 
    current_user: User,
    start_date: datetime, 
    end_date: datetime
  ) -> list[CompanyMemberAverageScore]:
    # Якщо користувач не передав дати — беремо поточний тиждень
    start_date, end_date = normalize_timestamps(start_date, end_date)
    logger.info(f"Fetching company members scores for company {company_id} by user {current_user.id}")
    await self.company_member_service.check_owner_or_admin(company_id, current_user.id)
    result = await self.repo.get_company_members_scores(company_id, start_date, end_date)
    if not result:
      logger.warning(f"No quiz timestamps found for company {company_id} between {start_date} and {end_date}")
      raise AnalyticsNotFound("Quiz timestamps not found")
    # Перетворюємо у список Pydantic-моделей
    return [
      CompanyMemberAverageScore.model_validate(row)
      for row in result
    ]

  # Список середніх балів для кожного тесту, пройденого вибраним користувачем з часовими діапазонами
  async def get_company_average_scores_quizzes(
    self, 
    company_id: UUID, 
    current_user: User,
    target_user_id: UUID, 
    start_date: datetime, 
    end_date: datetime
  ) -> CompanyQuizAverageScore:
    # Якщо користувач не передав дати — беремо поточний тиждень
    start_date, end_date = normalize_timestamps(start_date, end_date)
    logger.info(f"Fetching detailed quiz scores for user {target_user_id} in company {company_id}")
    await self.company_member_service.check_owner_or_admin(company_id, current_user.id)
    result = await self.repo.get_company_average_scores_quizzes(company_id, target_user_id, start_date, end_date)
    if not result:
      logger.warning(f"No quiz timestamps found for company {company_id} for user_id={target_user_id} between {start_date} and {end_date}")
      raise AnalyticsForbidden("Access denied to company analytics")
    # формуємо Pydantic-модель із всіх рядків
    user_data = {
      "user_id": result[0]["user_id"],
      "username": result[0]["username"],
      "average_scores_quizzes": [
        QuizAverageScore.model_validate(row) for row in result
      ]
    }
    return CompanyQuizAverageScore.model_validate(user_data)

  # Список всіх користувачів компанії та позначки часу їхньої останньої спроби пройти тест
  async def get_company_members_last_attempts(
    self, 
    company_id: UUID, 
    current_user: User
  ) -> CompanyMemberLastAttemptsResponse:
    logger.info(f"Fetching last quiz attempts for all members of company {company_id}")
    await self.company_member_service.check_owner_or_admin(company_id, current_user.id)
    company, members_rows = await self.repo.get_company_members_last_attempts(company_id)
    if not company:
      logger.warning(f"Company not found company_id={company_id}")
      raise CompanyNotFound()
    company_data = {
      "company_id": company["company_id"],
      "name": company["name"],
      "description": company["description"],
      "list_company_members": [
        CompanyMemberLastAttempt.model_validate(row) for row in members_rows
      ]
    }
    return CompanyMemberLastAttemptsResponse.model_validate(company_data)
