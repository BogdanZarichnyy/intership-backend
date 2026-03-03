from fastapi import APIRouter, Depends, Query, status
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.postgres import get_db
from app.schemas.quiz import QuizCreateRequest, QuizUpdateRequest, QuizSchema, QuizListResponse
from app.services.quiz import QuizService
from app.repositories.quiz import QuizRepository
from app.repositories.company_member import CompanyMemberRepository
from app.core.dependencies import get_current_user
from app.schemas.user import UserDetailResponse

router = APIRouter(tags=["quizzes"])

# Dependency
def get_quiz_service(db: AsyncSession = Depends(get_db)) -> QuizService:
  return QuizService(QuizRepository(db), CompanyMemberRepository(db))

@router.post(
  "/{company_id}", 
  response_model=QuizSchema, 
  status_code=status.HTTP_201_CREATED
)
async def create_quiz(
  company_id: UUID,
  quiz_data: QuizCreateRequest,
  current_user: UserDetailResponse = Depends(get_current_user),
  service: QuizService = Depends(get_quiz_service)
):
  return await service.create_quiz(company_id, current_user, quiz_data)

@router.get(
  "/{company_id}", 
  response_model=QuizListResponse, 
  status_code=status.HTTP_200_OK
)
async def list_quizzes(
  company_id: UUID,
  limit: int = Query(10, ge=1, le=100),
  offset: int = Query(0, ge=0),
  current_user: UserDetailResponse = Depends(get_current_user),
  service: QuizService = Depends(get_quiz_service)
):
  return await service.get_quizzes(company_id, current_user, limit, offset)

@router.get(
  "/detail/{quiz_id}", 
  response_model=QuizSchema, 
  status_code=status.HTTP_200_OK
)
async def get_quiz(
  quiz_id: UUID,
  current_user: UserDetailResponse = Depends(get_current_user),
  service: QuizService = Depends(get_quiz_service)
):
  return await service.get_quiz(quiz_id, current_user)

@router.patch(
  "/detail/{quiz_id}", 
  response_model=QuizSchema, 
  status_code=status.HTTP_200_OK
)
async def update_quiz(
  quiz_id: UUID,
  update_data: QuizUpdateRequest,
  current_user: UserDetailResponse = Depends(get_current_user),
  service: QuizService = Depends(get_quiz_service)
):
  return await service.update_quiz(quiz_id, current_user, update_data)

@router.delete(
  "/detail/{quiz_id}", 
  status_code=status.HTTP_204_NO_CONTENT
)
async def delete_quiz(
  quiz_id: UUID,
  current_user: UserDetailResponse = Depends(get_current_user),
  service: QuizService = Depends(get_quiz_service)
):
  await service.delete_quiz(quiz_id, current_user)
  return
