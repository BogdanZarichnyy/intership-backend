import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.postgres import get_db

DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres"

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(
  engine, class_=AsyncSession, expire_on_commit=False
)

@pytest.fixture
async def db_session():
  async with AsyncSessionLocal() as session:
    yield session

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
