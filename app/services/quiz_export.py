from uuid import UUID
from app.db.redis import redis_client
from app.models.quiz_workflow import QuizWorkflow
from app.repositories.quiz_workflow import QuizWorkflowRepository
from app.services.quiz import QuizService
from app.models.user import User
from app.utils.export_from_redis import generate_csv, generate_json
import json
from app.core.logger import logger
from app.core.exceptions import QuizExportForbidden, QuizExportNotFound, QuizExportCacheError

class QuizExportService:
  def __init__(self, result_repo: QuizWorkflowRepository, quiz_service: QuizService):
    self.result_repo = result_repo
    self.quiz_service = quiz_service
    self.redis = redis_client

  async def get_user_attempts(
    self, 
    company_id: UUID, 
    user_id: UUID, 
    current_user: User
  ) -> list[dict]:
    # Перевірка доступу
    member = await self.quiz_service.member_repo.get_member_of_company(company_id, current_user.id)
    if current_user.id != user_id:
      await self.quiz_service.check_owner_or_admin(company_id, current_user.id)
    elif not member:
      logger.warning(f"User {current_user.id} tried to access own results but is not a member")
      raise QuizExportForbidden()
    results: list[QuizWorkflow] = await self.result_repo.get_user_results(user_id, company_id)
    if not results:
      logger.info(f"No quiz results found for user {user_id} in company {company_id}")
      raise QuizExportNotFound()
    export_data = []
    for r in results:
      redis_key = f"quiz_attempt:{user_id}:{r.quiz_id}:{r.id}"
      try:
        raw = await self.redis.get(redis_key)
        if raw:
          attempt_data = json.loads(raw)
        else:
          # fallback на Postgres без answers
          attempt_data = {
            "attempt_id": str(r.id),
            "user_id": str(r.user_id),
            "company_id": str(r.company_id),
            "quiz_id": str(r.quiz_id),
            "answers": [],
            "total_questions": r.total_questions,
            "correct_answers": r.correct_answers,
            "score": r.score,
          }
      except Exception:
        logger.error(f"Redis error for key {redis_key}")
        raise QuizExportCacheError()
      export_data.append(attempt_data)
    logger.info(f"Prepared {len(export_data)} attempts for user {user_id}")
    return export_data

  async def get_quiz_attempts(
    self, 
    company_id: UUID, 
    quiz_id: UUID, 
    current_user: User
  ) -> list[dict]:
    await self.quiz_service.check_owner_or_admin(company_id, current_user.id)
    results: list[QuizWorkflow] = await self.result_repo.get_quiz_results(quiz_id, company_id)
    if not results:
      logger.info(f"No quiz results found for quiz {quiz_id} in company {company_id}")
      raise QuizExportNotFound()
    export_data = []
    for r in results:
      redis_key = f"quiz_attempt:{r.user_id}:{r.quiz_id}:{r.id}"
      try:
        raw = await self.redis.get(redis_key)
        if raw:
          attempt_data = json.loads(raw)
        else:
          attempt_data = {
            "attempt_id": str(r.id),
            "user_id": str(r.user_id),
            "company_id": str(r.company_id),
            "quiz_id": str(r.quiz_id),
            "answers": [],
            "total_questions": r.total_questions,
            "correct_answers": r.correct_answers,
            "score": r.score,
          }
      except Exception:
        logger.error(f"Redis error for key {redis_key}")
        raise QuizExportCacheError()
      export_data.append(attempt_data)
    logger.info(f"Prepared {len(export_data)} attempts for quiz {quiz_id}")
    return export_data

  def prepare_csv_rows(
    self, 
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
      else:
        for q in answers:
          for opt in q.get("selected_option_ids", []):
            rows.append({
              "attempt_id": attempt["attempt_id"],
              "user_id": attempt["user_id"],
              "company_id": attempt["company_id"],
              "quiz_id": attempt["quiz_id"],
              "question_id": q.get("question_id"),
              "selected_option_id": opt.get("answer"),
              "is_correct": opt.get("is_correct"),
              "score": attempt["score"],
              "correct_answers": attempt["correct_answers"],
              "total_questions": attempt["total_questions"],
            })
    return rows

  def export_json(
    self, 
    data: list[dict]
  ) -> str:
    return generate_json(data)

  def export_csv(
    self, 
    data: list[dict]
  ):
    rows = self.prepare_csv_rows(data)
    return generate_csv(rows)
