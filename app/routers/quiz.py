from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from app.core.dependencies import get_current_user, get_quiz_service
from app.models.user import User
from app.schemas.quiz import QuizCreateRequest, QuizUpdateRequest, QuizSchema, QuizListResponse
from app.services.quiz import QuizService

router = APIRouter(tags=["quizzes"])

@router.post(
  "/company/{company_id}", 
  response_model=QuizSchema, 
  status_code=status.HTTP_201_CREATED
)
async def create_quiz(
  company_id: UUID,
  quiz_data: QuizCreateRequest,
  current_user: User = Depends(get_current_user),
  service: QuizService = Depends(get_quiz_service)
):
  return await service.create_quiz(company_id, current_user, quiz_data)

@router.get(
  "/company/{company_id}", 
  response_model=QuizListResponse, 
  status_code=status.HTTP_200_OK
)
async def list_quizzes(
  company_id: UUID,
  limit: int = Query(10, ge=1, le=100),
  offset: int = Query(0, ge=0),
  current_user: User = Depends(get_current_user),
  service: QuizService = Depends(get_quiz_service)
):
  return await service.get_quizzes(company_id, current_user, limit, offset)

@router.get(
  "/company/{company_id}/quiz-detail/{quiz_id}", 
  response_model=QuizSchema, 
  status_code=status.HTTP_200_OK
)
async def get_quiz(
  company_id: UUID,
  quiz_id: UUID,
  current_user: User = Depends(get_current_user),
  service: QuizService = Depends(get_quiz_service)
):
  return await service.get_quiz(company_id, quiz_id, current_user)

@router.patch(
  "/company/{company_id}/quiz-detail/{quiz_id}", 
  response_model=QuizSchema, 
  status_code=status.HTTP_200_OK
)
async def update_quiz(
  company_id: UUID,
  quiz_id: UUID,
  update_data: QuizUpdateRequest,
  current_user: User = Depends(get_current_user),
  service: QuizService = Depends(get_quiz_service)
):
  return await service.update_quiz(company_id, quiz_id, current_user, update_data)

@router.delete(
  "/company/{company_id}/quiz-detail/{quiz_id}", 
  status_code=status.HTTP_204_NO_CONTENT
)
async def delete_quiz(
  company_id: UUID,
  quiz_id: UUID,
  current_user: User = Depends(get_current_user),
  service: QuizService = Depends(get_quiz_service)
):
  await service.delete_quiz(company_id, quiz_id, current_user)
