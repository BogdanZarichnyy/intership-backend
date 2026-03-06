from datetime import datetime
from uuid import UUID
from app.core.exceptions import AnalyticsNotFound, AnalyticsForbidden
from app.core.logger import logger
from app.models.user import User
from app.repositories.analytics import AnalyticsRepository
from app.services.quiz import QuizService
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
from app.utils.timestamps_format import timestamps_format

class AnalyticsService:
  def __init__(self, repo: AnalyticsRepository, quiz_service: QuizService):
    self.repo = repo
    self.quiz_service = quiz_service

  # =============================
  # User analytics
  # =============================

  # Загальний рейтинг користувача - середній бал за всі квізи
  async def get_user_overall_rating_service(
    self, 
    current_user: User
  ) -> UserOverallRatingResponse:
    logger.info(f"Calculating overall score for user {current_user.id}")
    rating = await self.repo.get_user_overall_rating_repo(current_user.id)
    if rating is None:
      logger.warning(f"No analytics found for user_id={current_user.id}")
      raise AnalyticsNotFound("User analytics not found")
    return round(float(rating), 2)


  # Список середніх балів для кожного квізу, 
  # пройденого користувачем, з часовими діапазонами
  async def get_user_average_scores_service(
    self, 
    current_user: User
  ) -> list[UserQuizAverageScoreResponse]:
    result: list[dict] = await self.repo.get_user_average_scores_repo(current_user.id)
    if not result:
      logger.warning(f"No quiz analytics found for user_id={current_user.id}")
      raise AnalyticsNotFound("User quiz analytics not found")
    logger.info(f"Fetching per-quiz scores for user {current_user.id}")
    return [
      UserQuizAverageScoreResponse(
        quiz_id=row["id"],
        title=row["title"],
        average_score=round(float(row["average_score"] or 0.0), 2),
        last_attempt=row["last_attempt"]
      )
      for row in result
    ]

  # Список тестів разом з часовими позначками їх останнього виконання
  async def get_user_quiz_last_attempts(
    self, 
    current_user: User
  ) -> list[UserQuizLastAttemptResponse]:
    logger.info(f"Fetching last quizzes attempts for user {current_user.id}")
    result: list[dict] = await self.repo.get_user_quizzes_with_timestamps()
    return [
      UserQuizLastAttemptResponse(
        id=row["id"],
        title=row["title"],
        updated_at=row["updated_at"]
      )
      for row in result
    ]

  # =============================
  # Company analytics
  # =============================

  # Список середніх балів всіх членів компанії з часовими діапазонами
  async def get_company_members_scores(
    self, 
    company_id: UUID, 
    user_id: UUID, 
    start_date: datetime, 
    end_date: datetime
  ) -> list[CompanyMemberAverageScore]:
    # Якщо користувач не передав дати — беремо поточний тиждень
    start_date, end_date = timestamps_format(start_date, end_date)
    logger.info(f"Fetching company members scores for company {company_id} by user {user_id}")
    await self.quiz_service.check_owner_or_admin(company_id, user_id)
    result: list[dict] = await self.repo.get_company_members_scores(company_id, start_date, end_date)
    if not result:
      logger.warning(f"No quiz timestamps found")
      raise AnalyticsNotFound("Quiz timestamps not found")
    # Перетворюємо у список Pydantic-моделей
    return [
      CompanyMemberAverageScore(
        user_id=row["id"],
        username=row["username"],
        average_score=round(float(row["average_score"] or 0.0), 2),
        last_attempt=row["last_attempt"]
      )
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
    start_date, end_date = timestamps_format(start_date, end_date)
    logger.info(f"Fetching detailed quiz scores for user {target_user_id} in company {company_id}")
    await self.quiz_service.check_owner_or_admin(company_id, current_user.id)
    result = await self.repo.get_company_average_scores_quizzes(company_id, target_user_id, start_date, end_date)
    if not result:
      logger.warning(f"Forbidden analytics access company_id={company_id} user_id={target_user_id}")
      raise AnalyticsForbidden("Access denied to company analytics")
    # Перетворюємо у список Pydantic-моделей
    if not result:
      return CompanyQuizAverageScore(
        user_id=target_user_id,
        username="",
        average_scores_quizzes=[]
      )
    return CompanyQuizAverageScore(
      user_id=result["user_id"],
      username=result["username"],
      average_scores_quizzes=[
        QuizAverageScore(**quiz) for quiz in result["average_scores_quizzes"]
      ]
    )

  # Список всіх користувачів компанії та позначки часу їхньої останньої спроби пройти тест
  async def get_company_members_last_attempts(
    self, 
    company_id: UUID, 
    user_id: UUID
  ) -> CompanyMemberLastAttemptsResponse:
    logger.info(f"Fetching last quiz attempts for all members of company {company_id}")
    await self.quiz_service.check_owner_or_admin(company_id, user_id)
    result = await self.repo.get_company_members_last_attempts(company_id)
    if not result:
      logger.warning(f"Forbidden analytics access company_id={company_id}")
      raise AnalyticsForbidden("Access denied to company analytics")
    return CompanyMemberLastAttemptsResponse(
      id=result["id"],
      name=result["name"],
      description=result["description"],
      list_company_members=[
        CompanyMemberLastAttempt(**member) for member in result["list_company_members"]
      ]
    )
