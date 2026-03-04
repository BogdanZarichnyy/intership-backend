import json
from uuid import UUID
from app.config import settings
from app.db.redis import redis_client
import redis.exceptions
from app.core.logger import logger

class QuizAttemptCacheService:
  def __init__(self, redis=redis_client):
    self.redis = redis

  def _build_key(self, user_id: UUID, quiz_id: UUID) -> str:
    # ключ у форматі: quiz_attempt:{user_id}:{quiz_id}
    return f"quiz_attempt:{user_id}:{quiz_id}"

  async def save_attempt(
    self,
    attempt_id: UUID,
    user_id: UUID,
    company_id: UUID,
    quiz_id: UUID,
    answers: list[dict],
    total_questions: int,
    correct_answers: int,
    score: float,
  ) -> None:
    key = self._build_key(user_id, quiz_id)
    payload = {
      "attempt_id": str(attempt_id),
      "user_id": str(user_id),
      "company_id": str(company_id),
      "quiz_id": str(quiz_id),
      "answers": answers,
      "total_questions": total_questions,
      "correct_answers": correct_answers,
      "score": score,
    }
    try:
      await self.redis.set(
        key, json.dumps(payload, indent=2, ensure_ascii=False), ex=settings.redis_ttl_seconds  # 48 годин
      )
      logger.info(f"Saved quiz attempt in Redis (user={user_id}, quiz={quiz_id})")
    except redis.exceptions.RedisError as error:
      logger.error(f"Failed to save quiz attempt in Redis: {error}")

  async def get_attempt(
    self, 
    company_id: UUID,
    quiz_id: UUID,
    user_id: UUID,
    attempt_id: UUID
  ) -> dict:
    key = self._build_key(company_id, quiz_id, user_id, attempt_id)
    try:
      raw = await self.redis.get(key)
      if not raw:
        logger.warning(f"Quiz attempt not found in Redis (user={user_id}, quiz={quiz_id})")
        return None
      logger.debug(f"Fetched quiz attempt from Redis (user={user_id}, quiz={quiz_id})")
      return json.loads(raw)
    except redis.exceptions.RedisError as error:
      logger.error(f"Failed to fetch quiz attempt from Redis: {error}")
      return None

  async def delete_attempt(
    self, 
    company_id: UUID,
    quiz_id: UUID,
    user_id: UUID,
    attempt_id: UUID
  ):
    key = self._build_key(company_id, quiz_id, user_id, attempt_id)
    try:
      deleted = await self.redis.delete(key)
      if deleted == 0:
        logger.debug(f"Tried to delete non-existent quiz attempt (user={user_id}, quiz={quiz_id})")
      else:
        logger.debug(f"Deleted quiz attempt from Redis (user={user_id}, quiz={quiz_id})")
    except redis.exceptions.RedisError as e:
      logger.error(f"Redis error while deleting quiz attempt (user={user_id}, quiz={quiz_id}): {e}")
