import pytest
from uuid import uuid4
from types import SimpleNamespace
from datetime import datetime, timezone
from app.services.notification import NotificationService
from app.schemas.notification import NotificationSchema
from app.core.exceptions import NotificationForbidden


# -------------------------
# FAKES
# -------------------------

class FakeNotificationRepo:
    def __init__(self):
        self.notifications = []
        self.updated = None

    async def create_notifications_bulk(self, notifications):
        self.notifications.extend(notifications)

    async def get_user_notifications(self, user_id):
        return [
            SimpleNamespace(
                **n,
                id=uuid4(),
                is_read=n.get("is_read", False),
                created_at=datetime.now(timezone.utc)
            )
            for n in self.notifications
            if n["user_id"] == user_id
        ]

    async def get_notification_by_id(self, notification_id):
        if self.notifications:
            n = self.notifications[0]
            return SimpleNamespace(
                id=notification_id,
                user_id=n["user_id"],
                quiz_id=n["quiz_id"],
            )
        return None

    async def update_notification_status(self, notification_id, current_user_id, is_read):
        self.updated = (notification_id, current_user_id, is_read)
        return SimpleNamespace(
            id=notification_id,
            user_id=current_user_id,
            quiz_id=uuid4(),
            message="test",
            is_read=is_read,
            created_at=datetime.now(timezone.utc),
        )


class FakeCompanyRepo:
    async def get_company_by_id(self, company_id):
        return SimpleNamespace(id=company_id)


class FakeMemberRepo:
    def __init__(self, has_member=True):
        self.has_member = has_member

    async def get_all_members_for_notifications(self, company_id):
        return [
            SimpleNamespace(member_id=uuid4()),
            SimpleNamespace(member_id=uuid4()),
        ]

    async def get_member_of_company(self, company_id, user_id):
        return SimpleNamespace(member_id=user_id) if self.has_member else None


# -------------------------
# FIXTURE
# -------------------------

@pytest.fixture
def service():
    return NotificationService(
        notification_repo=FakeNotificationRepo(),
        company_repo=FakeCompanyRepo(),
        member_repo=FakeMemberRepo(),
    )


# -------------------------
# TESTS
# -------------------------

@pytest.mark.asyncio
async def test_create_notifications(service):
    company_id = uuid4()
    quiz_id = uuid4()

    await service.create_notification_quiz(
      company_id=company_id,
      quiz_id=quiz_id,
      message="hello"
    )

    assert len(service.notification_repo.notifications) == 2


@pytest.mark.asyncio
async def test_get_notifications_for_user(service):
    user_id = uuid4()
    company_id = uuid4()

    service.notification_repo.notifications = [
        {"user_id": user_id, "quiz_id": uuid4(), "message": "x"}
    ]

    result = await service.get_notifications_for_user(
        company_id=company_id,
        current_user=SimpleNamespace(id=user_id)
    )

    assert len(result) == 1
    assert isinstance(result[0], NotificationSchema)


@pytest.mark.asyncio
async def test_mark_notification_as_read(service):
    user_id = uuid4()
    notification_id = uuid4()

    service.notification_repo.notifications = [
        {"user_id": user_id, "quiz_id": uuid4(), "message": "x"}
    ]

    result = await service.mark_notification_as_read(
        notification_id=notification_id,
        current_user=SimpleNamespace(id=user_id)
    )

    assert result.is_read is True


@pytest.mark.asyncio
async def test_forbidden_mark_notification(service):
    user_id = uuid4()

    service.notification_repo.notifications = [
        {"user_id": uuid4(), "quiz_id": uuid4(), "message": "x"}
    ]

    with pytest.raises(NotificationForbidden):
        await service.mark_notification_as_read(
            notification_id=uuid4(),
            current_user=SimpleNamespace(id=user_id)
        )
