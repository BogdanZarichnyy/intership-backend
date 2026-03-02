from fastapi import APIRouter, Depends, status
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.postgres import get_db
from app.schemas.quiz_result import QuizAttemptRequest, QuizAttemptResponse, UserQuizStatsResponse
from app.services.quiz_result import QuizResultService
from app.repositories.quiz_result import QuizResultRepository
from app.repositories.quiz import QuizRepository
from app.core.dependencies import get_current_user
from app.schemas.user import UserDetailResponse

router = APIRouter(tags=["quiz_results"])

def get_quiz_result_service(db: AsyncSession = Depends(get_db)) -> QuizResultService:
  return QuizResultService(QuizResultRepository(db), QuizRepository(db))

@router.post(
  "/{company_id}/{quiz_id}/attempt",
  response_model=QuizAttemptResponse,
  status_code=status.HTTP_201_CREATED
)
async def attempt_quiz(
  company_id: UUID,
  quiz_id: UUID,
  payload: QuizAttemptRequest,
  current_user: UserDetailResponse = Depends(get_current_user),
  service: QuizResultService = Depends(get_quiz_result_service)
):
  return await service.attempt_quiz(company_id, quiz_id, payload, current_user)

@router.get(
  "/{company_id}/user/{user_id}/stats",
  response_model=UserQuizStatsResponse,
  status_code=status.HTTP_200_OK
)
async def get_user_stats(
  company_id: UUID,
  user_id: UUID,
  current_user: UserDetailResponse = Depends(get_current_user),
  service: QuizResultService = Depends(get_quiz_result_service)
):
  return await service.get_user_stats(company_id, user_id)
