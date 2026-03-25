import pytest
from unittest.mock import AsyncMock
from uuid import uuid4

from app.services.quiz import QuizService
from app.models.user import User
from app.schemas.quiz import (
    QuizCreateRequest,
    QuizUpdateRequest,
    QuizQuestionSchema,
    QuizAnswerOptionSchema,
)


@pytest.fixture
def user():
    return User(id=uuid4())


@pytest.fixture
def service():
    return QuizService(
        quiz_repo=AsyncMock(),
        quiz_workflow_repo=AsyncMock(),
        member_repo=AsyncMock(),
        company_repo=AsyncMock(),
        company_member_service=AsyncMock(),
        notification_service=AsyncMock(),
    )

def make_quiz(**overrides):
  base = {
    "id": uuid4(),
    "company_id": uuid4(),
    "title": "quiz",
    "description": None,
    "participation_count": 0,
    "questions": [],
  }
  base.update(overrides)
  return type("Quiz", (), base)()

# =========================
# CREATE
# =========================

@pytest.mark.asyncio
async def test_create_quiz_success(service, user):
    company_id = uuid4()
    quiz_id = uuid4()

    service.company_repo.get_company_by_id.return_value = object()
    service.company_member_service.check_owner_or_admin.return_value = None
    service.quiz_repo.create_quiz.return_value = quiz_id
    service.quiz_repo.get_quiz_by_id.return_value = make_quiz(
      id=quiz_id,
      company_id=company_id,
      title="quiz",
      description=None,
      participation_count=0,
      questions=[]
    )

    service.notification_service.create_notification_quiz.return_value = None

    request = QuizCreateRequest(
        title="quiz",
        description=None,
        questions=[
            QuizQuestionSchema(
                title="q1",
                allows_multiple_correct=False,
                options=[
                    QuizAnswerOptionSchema(text="a", is_correct=True),
                    QuizAnswerOptionSchema(text="b", is_correct=False),
                ],
            ),
            QuizQuestionSchema(
                title="q2",
                allows_multiple_correct=False,
                options=[
                    QuizAnswerOptionSchema(text="a", is_correct=True),
                    QuizAnswerOptionSchema(text="b", is_correct=False),
                ],
            ),
        ],
    )

    result = await service.create_quiz(company_id, user, request)

    assert result.title == "quiz"
    service.quiz_repo.create_quiz.assert_called_once()


@pytest.mark.asyncio
async def test_create_quiz_fails_if_too_few_questions(service, user):
    company_id = uuid4()

    request = QuizCreateRequest(
        title="quiz",
        description=None,
        questions=[
            QuizQuestionSchema(
                title="q1",
                allows_multiple_correct=False,
                options=[
                    QuizAnswerOptionSchema(text="a", is_correct=True),
                    QuizAnswerOptionSchema(text="b", is_correct=False),
                ],
            )
        ],
    )

    service.company_repo.get_company_by_id.return_value = object()
    service.company_member_service.check_owner_or_admin.return_value = None

    with pytest.raises(Exception):
        await service.create_quiz(company_id, user, request)


# =========================
# GET QUIZ
# =========================

@pytest.mark.asyncio
async def test_get_quiz_success(service, user):
    company_id = uuid4()
    quiz_id = uuid4()

    service.company_repo.get_company_by_id.return_value = object()
    service.member_repo.get_member_of_company.return_value = object()

    service.quiz_repo.get_quiz_by_id.return_value = make_quiz(
        id=quiz_id,
        company_id=company_id,
        title="quiz",
        description=None,
        participation_count=0,
        questions=[]
    )

    result = await service.get_quiz(company_id, quiz_id, user)

    assert result.id == quiz_id


# =========================
# UPDATE QUIZ
# =========================

@pytest.mark.asyncio
async def test_update_quiz_success(service, user):
    company_id = uuid4()
    quiz_id = uuid4()

    service.company_member_service.check_owner_or_admin.return_value = None
    service.quiz_repo.get_quiz_by_id.return_value = make_quiz(
        id=quiz_id,
        company_id=company_id,
        title="quiz",
        description=None,
        participation_count=0,
        questions=[]
    )

    service.quiz_repo.update_quiz.return_value = None
    service.quiz_workflow_repo.delete_by_quiz_id.return_value = None
    service.notification_service.notification_repo.reset_notifications_for_quiz = AsyncMock()

    update = QuizUpdateRequest(
        title="updated",
        description=None,
        questions=[
            QuizQuestionSchema(
                title="q1",
                allows_multiple_correct=False,
                options=[
                    QuizAnswerOptionSchema(text="a", is_correct=True),
                    QuizAnswerOptionSchema(text="b", is_correct=False),
                ],
            ),
            QuizQuestionSchema(
                title="q2",
                allows_multiple_correct=False,
                options=[
                    QuizAnswerOptionSchema(text="a", is_correct=True),
                    QuizAnswerOptionSchema(text="b", is_correct=False),
                ],
            ),
        ],
    )

    result = await service.update_quiz(company_id, quiz_id, user, update)

    assert result is not None
    service.quiz_repo.update_quiz.assert_called_once()


# =========================
# DELETE
# =========================

@pytest.mark.asyncio
async def test_delete_quiz_success(service, user):
    company_id = uuid4()
    quiz_id = uuid4()

    service.company_member_service.check_owner_or_admin.return_value = None
    service.quiz_repo.get_quiz_by_id.return_value = type(
        "Quiz",
        (),
        {"id": quiz_id, "company_id": company_id}
    )()

    service.quiz_repo.delete_quiz.return_value = None

    await service.delete_quiz(company_id, quiz_id, user)

    service.quiz_repo.delete_quiz.assert_called_once_with(quiz_id)
