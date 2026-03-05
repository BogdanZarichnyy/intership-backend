from uuid import UUID
from fastapi import APIRouter, Depends, Query, status

from app.models.user import User
from app.services.quiz_export import QuizExportService
from app.core.dependencies import get_current_user, get_quiz_export_service
from app.utils.export_from_redis import export_response

router = APIRouter(tags=["quiz-export"])

@router.get(
  "/{company_id}/my", 
  status_code=status.HTTP_200_OK
)
async def export_my_results(
  company_id: UUID,
  format: str = Query("json", pattern="^(json|csv)$"),
  current_user: User = Depends(get_current_user),
  service: QuizExportService = Depends(get_quiz_export_service),
):
  data = await service.get_user_attempts(company_id, current_user)
  return export_response(current_user.id, data, format)

@router.get(
  "/{company_id}/user/{user_id}", 
  status_code=status.HTTP_200_OK
)
async def export_user_results(
  company_id: UUID,
  user_id: UUID,
  format: str = Query("json", pattern="^(json|csv)$"),
  current_user: User = Depends(get_current_user),
  service: QuizExportService = Depends(get_quiz_export_service),
):
  data = await service.get_user_attempts(company_id, current_user, user_id)
  return export_response(user_id, data, format)

@router.get(
  "/{company_id}/users", 
  status_code=status.HTTP_200_OK
)
async def export_all_users_results(
  company_id: UUID,
  format: str = Query("json", pattern="^(json|csv)$"),
  current_user: User = Depends(get_current_user),
  service: QuizExportService = Depends(get_quiz_export_service),
):
  data = await service.get_users_attempts(company_id, current_user)
  return export_response(company_id, data, format)

@router.get(
  "/{company_id}/quizzes/{quiz_id}",
  status_code=status.HTTP_200_OK,
)
async def export_quiz_results(
  company_id: UUID,
  quiz_id: UUID,
  format: str = Query("json", pattern="^(json|csv)$"),
  current_user: User = Depends(get_current_user),
  service: QuizExportService = Depends(get_quiz_export_service),
):
  data = await service.get_quiz_attempts(company_id, quiz_id, current_user)
  return export_response(quiz_id, data, format)
