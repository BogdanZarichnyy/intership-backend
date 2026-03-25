import pytest
from uuid import uuid4
from types import SimpleNamespace

from app.services.quiz_workflow_export import QuizExportService


class FakeRedisCache:
    def __init__(self):
        self.data = {
          "user": [{"attempt_id": "1"}],
          "company_user": [{"attempt_id": "2"}],
          "company": [{"attempt_id": "3"}],
          "quiz": [{"attempt_id": "4"}],
        }

    async def get_user_attempts(self, user_id):
        return self.data["user"]

    async def get_company_user_attempts(self, company_id, user_id):
        return self.data["company_user"]

    async def get_company_attempts(self, company_id):
        return self.data["company"]

    async def get_quiz_attempts(self, company_id, quiz_id):
        return self.data["quiz"]


class FakeCompanyMemberService:
    async def check_owner_or_admin(self, company_id, user_id):
        return True

    class company_repo:
        @staticmethod
        async def get_company_by_id(company_id):
            return SimpleNamespace(id=company_id)


class FakeQuizService:
    class member_repo:
        @staticmethod
        async def get_member_of_company(company_id, user_id):
            return True


@pytest.fixture
def service():
    return QuizExportService(
        quiz_service=FakeQuizService(),
        company_member_service=FakeCompanyMemberService(),
        redis_cache=FakeRedisCache(),
    )


@pytest.mark.asyncio
async def test_get_my_quiz_workflow_attempts(service):
    user = SimpleNamespace(id=uuid4())

    result = await service.get_my_quiz_workflow_attempts(user)

    assert len(result) == 1
    assert result[0]["attempt_id"] == "1"


@pytest.mark.asyncio
async def test_get_company_member_attempts(service):
    user = SimpleNamespace(id=uuid4())

    result = await service.get_company_member_quiz_workflow_attempts(
        company_id=uuid4(),
        current_user=user,
        user_id=uuid4()
    )

    assert len(result) == 1
    assert result[0]["attempt_id"] == "2"


@pytest.mark.asyncio
async def test_get_company_attempts(service):
    user = SimpleNamespace(id=uuid4())

    result = await service.get_company_members_quiz_workflow_attempts(
        company_id=uuid4(),
        current_user=user
    )

    assert len(result) == 1
    assert result[0]["attempt_id"] == "3"


@pytest.mark.asyncio
async def test_get_quiz_attempts(service):
    user = SimpleNamespace(id=uuid4())

    result = await service.get_company_quiz_workflow_attempts(
        company_id=uuid4(),
        quiz_id=uuid4(),
        current_user=user
    )

    assert len(result) == 1
    assert result[0]["attempt_id"] == "4"
