import pytest
from uuid import uuid4
from types import SimpleNamespace

from app.repositories.notification import NotificationRepository


class FakeSession:
    def __init__(self):
        self.executed = []
        self.committed = False

    async def execute(self, query):
        self.executed.append(query)

        # мінімальна симуляція SELECT
        class Result:
            def all(self): return []
            def scalar_one_or_none(self): return None
            def scalars(self): return self

        return Result()

    async def commit(self):
        self.committed = True


@pytest.fixture
def repo():
    return NotificationRepository(FakeSession())


@pytest.mark.asyncio
async def test_bulk_insert_empty(repo):
    result = await repo.create_notifications_bulk([])
    assert result is None


@pytest.mark.asyncio
async def test_bulk_insert(repo):
    notifications = [
        {"user_id": uuid4(), "quiz_id": uuid4(), "message": "x"}
    ]

    await repo.create_notifications_bulk(notifications)

    assert repo.db.committed is True


@pytest.mark.asyncio
async def test_upsert_empty(repo):
    await repo.upsert_notifications([])
    assert repo.db.committed is False
