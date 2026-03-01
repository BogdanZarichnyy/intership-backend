import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.db.postgres import Base, get_db
from app.main import app
import asyncio
import os
from alembic import command
from alembic.config import Config

# Тестова БД
TEST_DATABASE_URL = os.getenv(
  "TEST_DATABASE_URL",
  "postgresql+asyncpg://postgres:postgres@localhost:5433/internship_test_db"
)

# Асинхронний двигун для тестів
engine = create_async_engine(TEST_DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(
  engine, class_=AsyncSession, expire_on_commit=False
)

# Автоматичне застосування міграцій перед тестами
@pytest.fixture(scope="session", autouse=True)
def run_migrations():
  alembic_cfg = Config("alembic.ini")
  alembic_cfg.set_main_option("sqlalchemy.url", TEST_DATABASE_URL)
  command.upgrade(alembic_cfg, "head")

# Асинхронна сесія для тестів
@pytest.fixture
async def db_session():
  async with AsyncSessionLocal() as session:
    yield session

# Очистка таблиць після кожного тесту
@pytest.fixture(autouse=True)
async def clean_db(db_session: AsyncSession):
  yield
  # Очищаємо таблиці у зворотньому порядку (щоб не порушувати FK)
  for tbl in reversed(Base.metadata.sorted_tables):
    await db_session.execute(tbl.delete())
  await db_session.commit()

# HTTP-клієнт для тестів
@pytest.fixture
async def client(db_session):
  async def override_get_db():
    yield db_session

  app.dependency_overrides[get_db] = override_get_db
  transport = ASGITransport(app=app)
  async with AsyncClient(
    transport=transport,
    base_url="http://testserver"
  ) as client:
    yield client
  app.dependency_overrides.clear()
