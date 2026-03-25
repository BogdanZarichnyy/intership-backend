import pytest
from uuid import uuid4


# =========================
# FAKE REPOSITORY
# =========================

class FakeQuizRepo:
    def __init__(self):
        self.storage = {}

    async def create_quiz(self, quiz_data, questions_data):
        quiz_id = uuid4()
        self.storage[quiz_id] = {
            "id": quiz_id,
            "title": quiz_data["title"],
            "description": quiz_data.get("description"),
            "company_id": quiz_data["company_id"],
            "questions": questions_data,
        }
        return quiz_id

    async def get_quiz_by_id(self, quiz_id):
        data = self.storage.get(quiz_id)
        if not data:
            return None

        class Option:
            def __init__(self, text, is_correct):
                self.text = text
                self.is_correct = is_correct

        class Question:
            def __init__(self, q):
                self.id = uuid4()
                self.title = q["title"]
                self.allows_multiple_correct = q["allows_multiple_correct"]
                self.options = [
                    Option(o["text"], o["is_correct"]) for o in q["options"]
                ]

        class Quiz:
            pass

        quiz = Quiz()
        quiz.id = data["id"]
        quiz.title = data["title"]
        quiz.description = data["description"]
        quiz.company_id = data["company_id"]
        quiz.participation_count = 0

        quiz.questions = [Question(q) for q in data["questions"]]

        return quiz

    async def get_quizzes_for_company(self, company_id, limit, offset):
        return []


class FakeCompanyRepo:
    async def get_company_by_id(self, company_id):
        return type("Company", (), {"id": company_id, "owner_id": uuid4()})()


class FakeMemberRepo:
    async def get_member_of_company(self, company_id, user_id):
        return object()  # завжди член


class FakeCompanyMemberService:
    async def check_owner_or_admin(self, company_id, user_id):
        return True


class FakeNotificationService:
    async def create_notification_quiz(self, *args, **kwargs):
        return None


class FakeWorkflowRepo:
    async def delete_by_quiz_id(self, quiz_id):
        return None


# =========================
# TEST
# =========================

@pytest.mark.asyncio
async def test_quiz_service_create_flow():
    from app.services.quiz import QuizService
    from app.models.user import User
    from app.schemas.quiz import QuizCreateRequest, QuizQuestionSchema, QuizAnswerOptionSchema

    service = QuizService(
        quiz_repo=FakeQuizRepo(),
        quiz_workflow_repo=FakeWorkflowRepo(),
        member_repo=FakeMemberRepo(),
        company_repo=FakeCompanyRepo(),
        company_member_service=FakeCompanyMemberService(),
        notification_service=FakeNotificationService(),
    )

    user = User(id=uuid4())
    company_id = uuid4()

    request = QuizCreateRequest(
        title="integration",
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

    assert result.title == "integration"
    assert len(result.questions) == 2
