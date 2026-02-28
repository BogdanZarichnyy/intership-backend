from fastapi import APIRouter, Depends, Query
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.postgres import get_db
from app.schemas.quiz import (
  QuizCreateRequest, 
  QuizUpdateRequest, 
  QuizSchema, 
  QuizListResponse
)
from app.services.quiz import QuizService
from app.repositories.quiz import QuizRepository
from app.repositories.company_member import CompanyMemberRepository
from app.core.dependencies import get_current_user
from app.schemas.user import UserDetailResponse

router = APIRouter(tags=["quizzes"])

# Dependency
def get_quiz_service(db: AsyncSession = Depends(get_db)) -> QuizService:
  return QuizService(QuizRepository(db), CompanyMemberRepository(db))

# Створення тесту
@router.post(
  "/{company_id}", 
  response_model=QuizSchema
)
async def create_quiz(
  company_id: UUID, 
  quiz_data: QuizCreateRequest, 
  current_user: UserDetailResponse = Depends(get_current_user), 
  service: QuizService = Depends(get_quiz_service)
):
  quiz = await service.create_quiz(company_id, current_user.id, quiz_data)
  return quiz

# Список тестів компанії
@router.get(
  "/{company_id}", 
  response_model=QuizListResponse
)
async def list_quizzes(
  company_id: UUID, 
  limit: int = Query(10, ge=1, le=100), 
  offset: int = Query(0, ge=0), 
  current_user: UserDetailResponse = Depends(get_current_user), 
  service: QuizService = Depends(get_quiz_service)
):
  result = await service.get_quizzes(company_id, limit, offset)
  return QuizListResponse(quizzes=result["quizzes"], total=result["total"])

# Деталі одного тесту
@router.get(
  "/detail/{quiz_id}", 
  response_model=QuizSchema
)
async def get_quiz(
  quiz_id: UUID, 
  current_user: UserDetailResponse = Depends(get_current_user),
  service: QuizService = Depends(get_quiz_service)
):
  return await service.get_quiz(quiz_id)

# Оновлення тесту
@router.put(
  "/detail/{quiz_id}", 
  response_model=QuizSchema
)
async def update_quiz(
  quiz_id: UUID, 
  update_data: QuizUpdateRequest, 
  current_user: UserDetailResponse = Depends(get_current_user), 
  service: QuizService = Depends(get_quiz_service)
):
  return await service.update_quiz(quiz_id, current_user.id, update_data)

# Видалення тесту
@router.delete(
  "/detail/{quiz_id}"
)
async def delete_quiz(
  quiz_id: UUID, 
  current_user: UserDetailResponse = Depends(get_current_user), 
  service: QuizService = Depends(get_quiz_service)
):
  await service.delete_quiz(quiz_id, current_user.id)
  return {"detail": "Quiz deleted successfully"}

# Запис на проходження тесту,якщо буде потрібно (інкремент participation_count - змінюємо лічильник активності)
@router.post(
  "/detail/{quiz_id}/participate", 
  response_model=dict
)
async def participate_quiz(
  quiz_id: UUID,
  current_user: UserDetailResponse = Depends(get_current_user),
  service: QuizService = Depends(get_quiz_service)
):
  new_count = await service.record_participation(quiz_id)
  return {
    "quiz_id": quiz_id, 
    "new_participation_count": new_count
  }
