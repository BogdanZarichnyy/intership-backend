from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import StreamingResponse, JSONResponse

from app.models.user import User
from app.services.quiz_export import QuizExportService
from app.core.dependencies import get_current_user, get_quiz_export_service

router = APIRouter(tags=["quiz-export"])

# Експортувати спроби поточного користувача пройти тест для компанії у форматі JSON або CSV.
@router.get(
    "/my",
    status_code=status.HTTP_200_OK
)
async def export_my_results(
  company_id: UUID,
  format: str = Query("json", pattern="^(json|csv)$"),
  current_user: User = Depends(get_current_user),
  service: QuizExportService = Depends(get_quiz_export_service)
):
  data = await service.get_user_attempts(company_id, current_user.id, current_user)
  if format == "csv":
    csv_file = service.export_csv(data)
    return StreamingResponse(
      csv_file,
      media_type="text/csv",
      headers={"Content-Disposition": "attachment; filename=quiz_export.csv"}
    )
  return JSONResponse(content=data)

# Експорт спроб іншого користувача пройти тест для компанії (лише для адміністраторів/власників) у форматі JSON або CSV.
@router.get(
  "/users/{user_id}",
  status_code=status.HTTP_200_OK
)
async def export_user_results(
  company_id: UUID,
  user_id: UUID,
  format: str = Query("json", pattern="^(json|csv)$"),
  current_user: User = Depends(get_current_user),
  service: QuizExportService = Depends(get_quiz_export_service)
):
  data = await service.get_user_attempts(company_id, user_id, current_user)
  if format == "csv":
    csv_file = service.export_csv(data)
    return StreamingResponse(
      csv_file,
      media_type="text/csv",
      headers={"Content-Disposition": "attachment; filename=quiz_export.csv"}
    )
  return JSONResponse(content=data)

# Експортувати всі спроби для певної вікторини в компанії (лише для адміністраторів/власників) у форматі JSON або CSV.
@router.get(
  "/quizzes/{quiz_id}",
  status_code=status.HTTP_200_OK
)
async def export_quiz_results(
  company_id: UUID,
  quiz_id: UUID,
  format: str = Query("json", pattern="^(json|csv)$"),
  current_user: User = Depends(get_current_user),
  service: QuizExportService = Depends(get_quiz_export_service)
):
  data = await service.get_quiz_attempts(company_id, quiz_id, current_user)
  if format == "csv":
    csv_file = service.export_csv(data)
    return StreamingResponse(
      csv_file,
      media_type="text/csv",
      headers={"Content-Disposition": "attachment; filename=quiz_export.csv"}
    )
  return JSONResponse(content=data)
