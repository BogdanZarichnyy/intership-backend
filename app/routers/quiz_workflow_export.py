from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from app.core.dependencies import get_current_user, get_quiz_export_service
from app.models.user import User
from app.services.quiz_workflow_export import QuizExportService
from app.utils.quiz_workflow_export import export_response

router = APIRouter(tags=["quiz-workflow-export"])

# =====================================
# Отримати власний quiz
# =====================================
@router.get(
  "/my-quizzes", 
  status_code=status.HTTP_200_OK
)
async def export_my_results(
  format: str = Query("json", pattern="^(json|csv)$"),
  current_user: User = Depends(get_current_user),
  service: QuizExportService = Depends(get_quiz_export_service),
):
  data = await service.get_my_quiz_workflow_attempts(current_user)
  return export_response(data, format)

# =====================================
# Отримати quiz конкретного користувача
# =====================================
@router.get(
  "/company/{company_id}/member/{user_id}", 
  status_code=status.HTTP_200_OK
)
async def export_user_results(
  company_id: UUID,
  user_id: UUID,
  format: str = Query("json", pattern="^(json|csv)$"),
  current_user: User = Depends(get_current_user),
  service: QuizExportService = Depends(get_quiz_export_service),
):
  data = await service.get_company_member_quiz_workflow_attempts(company_id, current_user, user_id)
  return export_response(data, format)

# ====================================
# Отримати всі quizzes членів компанії
# ====================================
@router.get(
  "/company/{company_id}/members", 
  status_code=status.HTTP_200_OK
)
async def export_all_users_results(
  company_id: UUID,
  format: str = Query("json", pattern="^(json|csv)$"),
  current_user: User = Depends(get_current_user),
  service: QuizExportService = Depends(get_quiz_export_service),
):
  data = await service.get_company_members_quiz_workflow_attempts(company_id, current_user)
  return export_response(data, format)

# ============================================================
# Отримати результати конкретного quiz по всіх членах компанії
# ============================================================
@router.get(
  "/company/{company_id}/quiz/{quiz_id}",
  status_code=status.HTTP_200_OK,
)
async def export_quiz_results(
  company_id: UUID,
  quiz_id: UUID,
  format: str = Query("json", pattern="^(json|csv)$"),
  current_user: User = Depends(get_current_user),
  service: QuizExportService = Depends(get_quiz_export_service),
):
  data = await service.get_company_quiz_workflow_attempts(company_id, quiz_id, current_user)
  return export_response(data, format)
