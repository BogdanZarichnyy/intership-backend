import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock
from uuid import uuid4
from datetime import datetime, timezone

from app.main import app
from app.routers.quiz import QuizService
from app.schemas.quiz import QuizCreateRequest, QuizQuestionSchema, QuizAnswerOptionSchema

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

def make_quiz_create_request():
  return QuizCreateRequest(
    title="Sample Quiz",
    description="A simple test quiz",
    questions=[
      QuizQuestionSchema(
        title="Question 1",
        allows_multiple_correct=False,
        options=[
          QuizAnswerOptionSchema(text="Option A", is_correct=True),
          QuizAnswerOptionSchema(text="Option B", is_correct=False),
        ]
      ),
      QuizQuestionSchema(
        title="Question 2",
        allows_multiple_correct=True,
        options=[
          QuizAnswerOptionSchema(text="Option C", is_correct=True),
          QuizAnswerOptionSchema(text="Option D", is_correct=True),
          QuizAnswerOptionSchema(text="Option E", is_correct=False),
        ]
      ),
    ]
  )

@pytest.mark.asyncio
async def test_create_quiz(client: AsyncClient, company_id):
  mock_service = AsyncMock()
  mock_quiz = make_quiz_create_request()
  mock_service.create_quiz.return_value = mock_quiz
  app.dependency_overrides[QuizService] = lambda: mock_service

  response = await client.post(f"/quizzes/{company_id}", json=mock_quiz.dict())
  assert response.status_code == 200
  data = response.json()
  assert data["title"] == "Sample Quiz"
  assert len(data["questions"]) >= 2
  app.dependency_overrides = {}

@pytest.mark.asyncio
async def test_list_quizzes(client: AsyncClient, company_id):
  mock_service = AsyncMock()
  mock_service.get_quizzes.return_value = {"quizzes": [], "total": 0}
  app.dependency_overrides[QuizService] = lambda: mock_service

  response = await client.get(f"/quizzes/{company_id}?limit=10&offset=0")
  assert response.status_code == 200
  data = response.json()
  assert "quizzes" in data
  assert "total" in data
  app.dependency_overrides = {}

@pytest.mark.asyncio
async def test_get_quiz(client: AsyncClient, quiz_id):
  mock_service = AsyncMock()
  mock_service.get_quiz.return_value = {"id": str(quiz_id), "title": "Sample Quiz", "participation_count": 0, "questions": []}
  app.dependency_overrides[QuizService] = lambda: mock_service

  response = await client.get(f"/quizzes/detail/{quiz_id}")
  assert response.status_code == 200
  data = response.json()
  assert data["id"] == str(quiz_id)
  app.dependency_overrides = {}

@pytest.mark.asyncio
async def test_update_quiz(client: AsyncClient, quiz_id):
  mock_service = AsyncMock()
  update_data = {"title": "Updated Quiz"}
  mock_service.update_quiz.return_value = {"id": str(quiz_id), "title": "Updated Quiz", "questions": [], "participation_count": 0}
  app.dependency_overrides[QuizService] = lambda: mock_service

  response = await client.put(f"/quizzes/detail/{quiz_id}", json=update_data)
  assert response.status_code == 200
  data = response.json()
  assert data["title"] == "Updated Quiz"
  app.dependency_overrides = {}

@pytest.mark.asyncio
async def test_delete_quiz(client: AsyncClient, quiz_id):
  mock_service = AsyncMock()
  mock_service.delete_quiz.return_value = None
  app.dependency_overrides[QuizService] = lambda: mock_service

  response = await client.delete(f"/quizzes/detail/{quiz_id}")
  assert response.status_code == 200 or response.status_code == 204
  app.dependency_overrides = {}

@pytest.mark.asyncio
async def test_participate_quiz(client: AsyncClient, quiz_id):
  mock_service = AsyncMock()
  mock_service.record_participation.return_value = 5
  app.dependency_overrides[QuizService] = lambda: mock_service

  response = await client.post(f"/quizzes/detail/{quiz_id}/participate")
  assert response.status_code == 200
  data = response.json()
  assert data["quiz_id"] == str(quiz_id)
  assert data["new_participation_count"] == 5
  app.dependency_overrides = {}
