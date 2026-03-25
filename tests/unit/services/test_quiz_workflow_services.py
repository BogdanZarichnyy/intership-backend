import pytest
from uuid import uuid4
from types import SimpleNamespace
from datetime import datetime, timezone

from app.services.quiz_workflow import QuizWorkflowService
from app.schemas.quiz_workflow import QuizAttemptRequest, QuizAttemptAnswerSchema
from app.core.exceptions import QuizForbidden


class FakeQuizWorkflowRepo:
    async def increment_participation(self, quiz_id):
        return None

    async def create_quiz_workflow(self, quiz_workflow):
        return SimpleNamespace(
            id=uuid4(),
            quiz_id=quiz_workflow.quiz_id,
            company_id=quiz_workflow.company_id,
            user_id=quiz_workflow.user_id,
            correct_answers=quiz_workflow.correct_answers,
            total_questions=quiz_workflow.total_questions,
            score=quiz_workflow.score,
            updated_at=datetime.now(timezone.utc)  # FIX
        )


class FakeQuizService:
    def __init__(self, quiz):
        self.quiz_repo = self.Repo(quiz)

    class Repo:
        def __init__(self, quiz):
            self.quiz = quiz

        async def get_quiz_by_id(self, quiz_id):
            return self.quiz


class FakeMemberRepo:
    async def get_member_of_company(self, *args, **kwargs):
        return True


class FakeCompanyMemberService:
    async def check_owner_or_admin(self, *args, **kwargs):
        return True


class FakeRedisCache:
    async def save_attempt(self, *args, **kwargs):
        return None


@pytest.mark.asyncio
async def test_attempt_quiz_success():
    quiz_id = uuid4()
    company_id = uuid4()

    opt1 = SimpleNamespace(id=uuid4(), is_correct=True)
    opt2 = SimpleNamespace(id=uuid4(), is_correct=False)

    question = SimpleNamespace(
        id=uuid4(),
        options=[opt1, opt2],
        allows_multiple_correct=False
    )

    quiz = SimpleNamespace(
        id=quiz_id,
        company_id=company_id,
        questions=[question],
        participation_count=0
    )

    service = QuizWorkflowService(
        quiz_workflow_repo=FakeQuizWorkflowRepo(),
        member_repo=FakeMemberRepo(),
        quiz_service=FakeQuizService(quiz),
        company_member_service=FakeCompanyMemberService(),
        redis_cache=FakeRedisCache()
    )

    payload = QuizAttemptRequest(
        answers=[
            QuizAttemptAnswerSchema(
                question_id=question.id,
                selected_option_ids=[opt1.id]
            )
        ]
    )

    result = await service.attempt_quiz(
        company_id=company_id,
        quiz_id=quiz_id,
        payload=payload,
        current_user=SimpleNamespace(id=uuid4())
    )

    assert result.quiz_id == quiz_id
    assert result.correct_answers == 1
    assert result.total_questions == 1
    assert 0.0 <= result.score <= 1.0


@pytest.mark.asyncio
async def test_attempt_quiz_wrong_company_forbidden():
    quiz_id = uuid4()
    company_id = uuid4()

    quiz = SimpleNamespace(
        id=quiz_id,
        company_id=company_id,
        questions=[],
        participation_count=0
    )

    service = QuizWorkflowService(
        quiz_workflow_repo=FakeQuizWorkflowRepo(),
        member_repo=FakeMemberRepo(),
        quiz_service=FakeQuizService(quiz),
        company_member_service=FakeCompanyMemberService(),
        redis_cache=FakeRedisCache()
    )

    payload = QuizAttemptRequest(answers=[])

    with pytest.raises(QuizForbidden):
      await service.attempt_quiz(
        company_id=uuid4(),
        quiz_id=quiz_id,
        payload=payload,
        current_user=SimpleNamespace(id=uuid4())
      )
