from uuid import UUID
import json
from datetime import datetime
from app.config import settings
from app.core.logger import logger
from app.db.redis import redis_client

class QuizAttemptCacheService:
  def __init__(self, redis=redis_client):
    self.redis = redis

  def _attempt_key(
    self,
    company_id: UUID,
    quiz_id: UUID,
    user_id: UUID,
    attempt_id: UUID
  ) -> str:
    # ключ у форматі: quiz_workflow_attempt_key:{company_id}:{quiz_id}:{user_id}:{attempt_id}
    return f"quiz_workflow_attempt_key:{company_id}:{quiz_id}:{user_id}:{attempt_id}"
  
  def _user_index_key(
    self,
    company_id: UUID,
    quiz_id: UUID,
    user_id: UUID
  ) -> str:
    return f"quiz_workflow_attempt_index_user_quiz:{company_id}:{quiz_id}:{user_id}"

  def _quiz_index_key(
    self,
    company_id: UUID,
    quiz_id: UUID
  ) -> str:
    return f"quiz_workflow_attempt_index_quiz:{company_id}:{quiz_id}"

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
    attempted_at: datetime
  ) -> None:
    attempt_key = self._attempt_key(company_id, quiz_id, user_id, attempt_id)
    user_index = self._user_index_key(company_id, quiz_id, user_id)
    quiz_index = self._quiz_index_key(company_id, quiz_id)
    payload = {
      "attempt_id": str(attempt_id),
      "user_id": str(user_id),
      "company_id": str(company_id),
      "quiz_id": str(quiz_id),
      "answers": json.dumps(answers, ensure_ascii=False),
      "total_questions": total_questions,
      "correct_answers": correct_answers,
      "score": score,
      "attempted_at": attempted_at.isoformat()
    }
    timestamp = attempted_at.timestamp()
    try:
      pipe = self.redis.pipeline(transaction=True)
      # attempt key
      pipe.hset(attempt_key, mapping=payload)
      pipe.expire(attempt_key, settings.redis_ttl_seconds)  # 48 годин
      # user index
      pipe.zadd(user_index, {str(attempt_id): timestamp})
      pipe.expire(user_index, settings.redis_ttl_seconds)   # 48 годин
      # quiz index
      pipe.zadd(quiz_index, {str(attempt_id): timestamp})
      pipe.expire(quiz_index, settings.redis_ttl_seconds)   # 48 годин
      await pipe.execute()
      logger.info(f"Quiz workflow attempt cached (company={company_id}, quiz={quiz_id}, user={user_id}, attempt={attempt_id})")
    except Exception as error:
      logger.error(f"Failed to save quiz attempt in Redis: {error}")

  async def get_attempt(
    self, 
    company_id: UUID,
    quiz_id: UUID,
    user_id: UUID,
    attempt_id: UUID
  ) -> dict:
    key = self._attempt_key(company_id, quiz_id, user_id, attempt_id)
    try:
      data = await self.redis.hgetall(key)
      if not data:
        logger.warning(f"Quiz attempt not found in Redis (user={user_id}, quiz={quiz_id})")
        return None
      if "answers" in data:
        data["answers"] = json.loads(data["answers"])
      logger.debug(f"Fetched quiz attempt from Redis (user={user_id}, quiz={quiz_id})")
      return data
    except Exception as error:
      logger.error(f"Failed to fetch quiz attempt from Redis: {error}")
      return None

  async def delete_attempt(
    self, 
    company_id: UUID,
    quiz_id: UUID,
    user_id: UUID,
    attempt_id: UUID
  ):
    key = self._attempt_key(company_id, quiz_id, user_id, attempt_id)
    try:
      deleted = await self.redis.delete(key)
      if deleted == 0:
        logger.debug(f"Tried to delete non-existent quiz attempt (user={user_id}, quiz={quiz_id})")
      else:
        logger.debug(f"Deleted quiz attempt from Redis (user={user_id}, quiz={quiz_id})")
    except Exception as e:
      logger.error(f"Redis error while deleting quiz attempt (user={user_id}, quiz={quiz_id}): {e}")
