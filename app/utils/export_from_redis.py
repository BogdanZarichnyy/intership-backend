from uuid import UUID
import json
import csv
from io import StringIO
from pathlib import Path
from redis.asyncio import Redis
from fastapi.responses import StreamingResponse, JSONResponse
from app.core.logger import logger
from app.core.exceptions import QuizExportCacheError

# базова папка проекту відносно цього файлу
# BASE_DIR = Path(__file__).resolve().parent.parent  # якщо сервіс у app/services
# Папка для збереження файлів
LOG_DIR = Path("logs/quiz_export")
LOG_DIR.mkdir(parents=True, exist_ok=True)

# -----------------------------
# INTERNAL REDIS SCAN
# -----------------------------
async def scan_attempts(
  redis_client: Redis, 
  pattern: str
) -> list[dict]:
  attempts = []
  try:
    async for key in redis_client.scan_iter(match=pattern):
      raw = await redis_client.get(key)
      if raw:
        attempts.append(json.loads(raw))
  except Exception:
    raise QuizExportCacheError()
  return attempts

# -----------------------------
# CSV PREPARATION
# -----------------------------
def _prepare_csv_rows(
  export_data: list[dict]
) -> list[dict]:
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
      })
      continue
    for question in answers:
      for opt in question.get("selected_option_ids", []):
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
        })
  return rows

# -----------------------------
# EXPORT TO JSON OR CSV FILE
# -----------------------------
def _export_response_to_file(
  target_id: UUID, 
  data: list[dict],
  format: str = "json"
) -> Path:
  filename = LOG_DIR / f"{target_id}.{format}"

  if format == "json":
    existing_data = []
    if filename.exists():
      with open(filename, "r", encoding="utf-8") as f:
        try:
          existing_data = json.load(f)
        except Exception:
          existing_data = []
    existing_ids = {item["attempt_id"] for item in existing_data}
    new_attempts = [attempt for attempt in data if attempt["attempt_id"] not in existing_ids]
    if new_attempts:
      existing_data.extend(new_attempts)
      with open(filename, "w", encoding="utf-8") as f:
        json.dump(existing_data, f, indent=2)
      logger.info(f"Added {len(new_attempts)} JSON attempts to {filename}")
    else:
      logger.info(f"No new JSON attempts for {filename}")
    return filename
  
  elif format == "csv":
    existing_rows = []
    existing_ids = set()
    if filename.exists():
      with open(filename, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        existing_rows = list(reader)
        existing_ids = {row["attempt_id"] for row in existing_rows}
    new_rows = []
    for attempt in data:
      if attempt["attempt_id"] in existing_ids:
        continue
      new_rows.extend(_prepare_csv_rows([attempt]))
    if new_rows:
      updated_rows = existing_rows + new_rows
      with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
          f,
          fieldnames=updated_rows[0].keys()
        )
        writer.writeheader()
        writer.writerows(updated_rows)
      logger.info(
        f"Added {len(new_rows)} CSV rows to {filename}"
      )
    else:
      logger.info(f"No new CSV rows for {filename}")
    return filename
  else:
    raise ValueError(f"Unsupported format: {format}")

# -----------------------------
# UNIFIED EXPORT RESPONSE
# -----------------------------
def export_response(
  target_id: UUID, 
  data: list[dict], 
  format: str = "json"
):
  if not data:
    logger.info("No quiz attempts found to export")
    return JSONResponse(content=[], status_code=404)
  # завжди зберігаємо у файл
  _export_response_to_file(target_id, data, format)
  if format == "csv":
    rows = _prepare_csv_rows(data)
    csv_buffer = StringIO()
    writer = csv.DictWriter(csv_buffer, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)
    csv_buffer.seek(0)
    return StreamingResponse(
      csv_buffer,
      media_type="text/csv",
      headers={"Content-Disposition": f"attachment; filename=quiz_export_{target_id}.csv"},
    )
  # формат JSON
  return JSONResponse(content=data)
