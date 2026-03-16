import pytest
import shutil
from pathlib import Path
from uuid import uuid4
from datetime import datetime, timezone
from unittest.mock import AsyncMock

from app.services.quiz_workflow_export import QuizExportService

EXPORT_DIR = Path("app/logs/quiz_export")

@pytest.fixture
def cleanup_exports():
  # Видаляємо старі тести перед запуском
  if EXPORT_DIR.exists():
    shutil.rmtree(EXPORT_DIR)
  EXPORT_DIR.mkdir(parents=True, exist_ok=True)
  yield
  # Очистка після тесту
  if EXPORT_DIR.exists():
    shutil.rmtree(EXPORT_DIR)

@pytest.fixture
def mock_quiz_service():
  service = AsyncMock()
  service.check_owner_or_admin.return_value = None
  return service

@pytest.fixture
def mock_member_repo():
  return AsyncMock()

def make_quiz_attempt(user_id=None, company_id=None, quiz_id=None):
  now = datetime.now(timezone.utc)
  return [{
    "attempt_id": str(uuid4()),
    "user_id": user_id or str(uuid4()),
    "company_id": company_id or str(uuid4()),
    "quiz_id": quiz_id or str(uuid4()),
    "answers": [],
    "total_questions": 5,
    "correct_answers": 3,
    "score": 0.6,
    "created_at": now.isoformat()
  }]

@pytest.mark.asyncio
async def test_quiz_export_json_and_csv(mock_quiz_service, mock_member_repo, cleanup_exports):
  user_id = str(uuid4())
  company_id = str(uuid4())

  service = QuizExportService(mock_quiz_service, mock_member_repo)

  # Перший експорт
  data1 = make_quiz_attempt(user_id=user_id, company_id=company_id)
  service.export_response(data1, "json")
  service.export_response(data1, "csv")

  # Другий експорт (інший квіз, того ж користувача)
  data2 = make_quiz_attempt(user_id=user_id, company_id=company_id)
  service.export_response(data2, "json")
  service.export_response(data2, "csv")

  # Перевіряємо JSON файл
  json_file = EXPORT_DIR / f"{user_id}.json"
  assert json_file.exists()
  content = json_file.read_text()
  assert data1[0]["attempt_id"] in content
  assert data2[0]["attempt_id"] in content

  # Перевіряємо CSV файл
  csv_file = EXPORT_DIR / f"{user_id}.csv"
  assert csv_file.exists()
  csv_content = csv_file.read_text()
  assert data1[0]["attempt_id"] in csv_content
  assert data2[0]["attempt_id"] in csv_content
