from uuid import UUID
from fastapi import APIRouter, Depends, status

from app.schemas.quiz_workflow import QuizAttemptRequest, QuizAttemptResponse, UserQuizStatsResponse
from app.services.quiz_workflow import QuizWorkflowService
from app.core.dependencies import get_current_user, get_quiz_workflow_service
from app.models.user import User

router = APIRouter(tags=["quiz-workflow"])

@router.post(
  "/{company_id}/{quiz_id}/attempt",
  response_model=QuizAttemptResponse,
  status_code=status.HTTP_201_CREATED
)
async def attempt_quiz(
  company_id: UUID,
  quiz_id: UUID,
  payload: QuizAttemptRequest,
  current_user: User = Depends(get_current_user),
  service: QuizWorkflowService = Depends(get_quiz_workflow_service)
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
  current_user: User = Depends(get_current_user),
  service: QuizWorkflowService = Depends(get_quiz_workflow_service)
):
  return await service.get_user_stats(company_id, user_id, current_user)
