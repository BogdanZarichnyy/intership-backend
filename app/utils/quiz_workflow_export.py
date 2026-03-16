import csv
from uuid import UUID
from io import StringIO
from fastapi.responses import StreamingResponse, JSONResponse
from app.core.logger import logger
from app.services.quiz_workflow_redis_cache import QuizAttemptCacheService

redis_cache = QuizAttemptCacheService()

# ===================================
# Підготовка CSV рядків із даних quiz
# ===================================
def prepare_csv_rows(export_data: list[dict]) -> list[dict]:
  rows = []
  for attempt in export_data:
    answers = attempt.get("answers") or []
    if not answers:
      rows.append({
        "attempt_id": attempt["attempt_id"],
        "user_id": attempt["user_id"],
        "company_id": attempt["company_id"],
        "quiz_id": attempt["quiz_id"],
        "question_id": "",
        "selected_option_id": "",
        "is_correct": "",
        "score": attempt["score"],
        "correct_answers": attempt["correct_answers"],
        "total_questions": attempt["total_questions"],
        "attempted_at": attempt["attempted_at"],
      })
      continue
    for question in answers:
      for opt in question.get("selected_options", []):
        rows.append({
          "attempt_id": attempt["attempt_id"],
          "user_id": attempt["user_id"],
          "company_id": attempt["company_id"],
          "quiz_id": attempt["quiz_id"],
          "question_id": question.get("question_id"),
          "selected_option_id": opt.get("answer"),
          "is_correct": opt.get("is_correct"),
          "score": attempt["score"],
          "correct_answers": attempt["correct_answers"],
          "total_questions": attempt["total_questions"],
          "attempted_at": attempt["attempted_at"],
        })
  return rows

# =================================
# Єдиний метод для експорту у фронт
# =================================
def export_response(data: list[dict], format: str = "json"):
  if not data:
    logger.info("No quiz attempts found to export")
    return JSONResponse(content=[], status_code=404)
  if format == "csv":
    rows = prepare_csv_rows(data)
    if not rows:
      logger.info("No CSV rows to export")
      return JSONResponse(content=[], status_code=404)
    csv_buffer = StringIO()
    writer = csv.DictWriter(csv_buffer, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)
    csv_buffer.seek(0)
    return StreamingResponse(
      csv_buffer,
      media_type="text/csv",
      headers={"Content-Disposition": "attachment; filename=quiz_export.csv"},
    )
  # формат JSON
  return JSONResponse(content=data)

# ============================================================
# Експорт даних з Redis в CSV/JSON - для великих об'ємів даних
# ============================================================
async def export_quiz_csv(
  company_id: UUID,
  quiz_id: UUID,
  batch_size: int = 200
) -> bytes:
  """
  Експортує всі спроби конкретного quiz у CSV.
  Використовує батчі для ефективної роботи з Redis.
  """
  index_key = redis_cache._quiz_index(company_id, quiz_id)
  try:
    total = await redis_cache.redis.zcard(index_key)
    if total == 0:
      logger.info(f"No attempts found in Redis for quiz {quiz_id}")
      return b""
    output = StringIO()
    writer = csv.writer(output)
    # хедери CSV
    writer.writerow([
      "attempt_id",
      "user_id",
      "company_id",
      "quiz_id",
      "score",
      "total_questions",
      "correct_answers",
      "attempted_at",
      "answers"
    ])
    start = 0
    while start < total:
      # беремо batch ключів attempt
      attempt_ids = await redis_cache.redis.zrange(
        index_key,
        start,
        start + batch_size - 1
      )
      # отримуємо повні дані по batch
      attempts = await redis_cache._fetch_attempts_by_ids(attempt_ids)
      for attempt in attempts:
        writer.writerow([
          attempt.get("attempt_id"),
          attempt.get("user_id"),
          attempt.get("company_id"),
          attempt.get("quiz_id"),
          attempt.get("score"),
          attempt.get("total_questions"),
          attempt.get("correct_answers"),
          attempt.get("attempted_at"),
          attempt.get("answers"),
        ])
      start += batch_size
    output.seek(0)
    return output.getvalue().encode()
  except Exception as error:
    logger.error(f"Redis export error: {error}")
    raise
