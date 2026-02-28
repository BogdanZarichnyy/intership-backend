import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch
from uuid import uuid4
from datetime import datetime, timezone

from app.main import app
from app.routers.quiz_result import QuizResultService
from app.schemas.quiz_result import QuizAttemptRequest, QuizAttemptResponse, UserQuizStatsResponse
from app.services.quiz import QuizService

@pytest.fixture
async def client():
  async with AsyncClient(app=app, base_url="http://testserver") as ac:
    yield ac

@pytest.fixture
def company_id():
  return uuid4()

@pytest.fixture
def quiz_id():
  return uuid4()

@pytest.fixture
def user_id():
  return uuid4()

def make_quiz_attempt_request(quiz_id):
  return QuizAttemptRequest(
    answers=[
      {"question_id": uuid4(), "selected_option_ids": [uuid4()]},
      {"question_id": uuid4(), "selected_option_ids": [uuid4(), uuid4()]},
    ]
  )

@pytest.mark.asyncio
async def test_attempt_quiz_calls_participation(client: AsyncClient, quiz_id, user_id, company_id):
  # Моки сервісів
  mock_quiz_service = AsyncMock()
  mock_quiz_service.record_participation.return_value = 10  # новий лічильник
  mock_service = AsyncMock()
  mock_service.attempt_quiz.side_effect = lambda *args, **kwargs: QuizAttemptResponse(
    quiz_id=quiz_id,
    user_id=user_id,
    correct_answers=2,
    total_questions=2,
    score=1.0,
    attempted_at=datetime.now(timezone.utc)
)

  # Перекриваємо залежності
  app.dependency_overrides[QuizResultService] = lambda: mock_service
  app.dependency_overrides[QuizService] = lambda: mock_quiz_service

  payload = make_quiz_attempt_request(quiz_id)
  response = await client.post(f"/quiz_results/{company_id}/{quiz_id}/attempt", json=payload.dict())
  
  assert response.status_code == 200
  data = response.json()
  assert data["quiz_id"] == str(quiz_id)
  assert data["user_id"] == str(user_id)
  assert data["score"] == 1.0

  # Перевіряємо, що лічильник участі було викликано
  mock_quiz_service.record_participation.assert_called_once_with(quiz_id)

  app.dependency_overrides = {}
