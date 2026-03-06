from uuid import UUID
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from app.core.dependencies import get_current_user, get_analytics_service
from app.models.user import User
from app.services.analytics import AnalyticsService

router = APIRouter(tags=["analytics"])

# ==========================================================
# Аналітика для кожного користувача
# ==========================================================

# Загальний рейтинг користувача - середній бал за всі квізи
@router.get(
  "/me/overall-rating",
  status_code=status.HTTP_200_OK
)
async def get_my_overall_rating(
  current_user: User = Depends(get_current_user),
  service: AnalyticsService = Depends(get_analytics_service)
):
  return {"overall_rating": await service.get_user_overall_rating_service(current_user)}

# Список середніх балів для кожного квізу, 
# пройденого користувачем, з часовими діапазонами
@router.get(
  "/me/average-scores", 
  status_code=status.HTTP_200_OK
)
async def get_my_average_scores(
  current_user: User = Depends(get_current_user),
  service: AnalyticsService = Depends(get_analytics_service)
):
  return await service.get_user_average_scores_service(current_user)

# Список тестів разом з часовими позначками їх останнього виконання
@router.get(
  "/me/quizzes", 
  status_code=status.HTTP_200_OK
)
async def get_my_last_attempts(
  current_user: User = Depends(get_current_user),
  service: AnalyticsService = Depends(get_analytics_service)
):
  return await service.get_user_quiz_last_attempts(current_user)

# ==========================================================
# Аналітика для власників та адміністраторів компанії
# ==========================================================

# Список середніх балів всіх членів компанії з часовими діапазонами
@router.get(
  "/company/{company_id}/average-scores-members", 
  status_code=status.HTTP_200_OK
)
async def get_company_members_scores(
  company_id: UUID,
  start_date: Optional[datetime] = None,
  end_date: Optional[datetime] = None,
  current_user: User = Depends(get_current_user),
  service: AnalyticsService = Depends(get_analytics_service)
):
  return await service.get_company_members_scores(company_id, current_user.id, start_date, end_date)

# Список середніх балів для кожного тесту, пройденого вибраним користувачем з часовими діапазонами
@router.get(
  "/company/{company_id}/user/{target_user_id}/average-scores-quizzes", 
  status_code=status.HTTP_200_OK
)
async def get_company_user_scores(
  company_id: UUID,
  target_user_id: UUID,
  start_date: Optional[datetime] = None,
  end_date: Optional[datetime] = None,
  current_user: User = Depends(get_current_user),
  service: AnalyticsService = Depends(get_analytics_service)
):
  return await service.get_company_average_scores_quizzes(company_id, current_user, target_user_id, start_date, end_date)

# Список всіх користувачів компанії та позначки часу їхньої останньої спроби пройти тест
@router.get(
  "/company/{company_id}/company-users-timestamps", 
  status_code=status.HTTP_200_OK
)
async def get_company_members_last_attempts(
  company_id: UUID,
  current_user: User = Depends(get_current_user),
  service: AnalyticsService = Depends(get_analytics_service)
):
  return await service.get_company_members_last_attempts(company_id, current_user.id)
