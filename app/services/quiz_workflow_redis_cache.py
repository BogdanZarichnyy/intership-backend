from uuid import UUID
import json
import redis.exceptions
from datetime import datetime
from app.config import settings
from app.core.logger import logger
from app.db.redis import redis_client

class QuizAttemptCacheService:
  def __init__(self, redis=redis_client):
    self.redis = redis

  # ---------- keys ----------

  def _attempt_key(self, attempt_id: UUID) -> str:
    return f"quiz_workflow_attempt:{attempt_id}"

  def _user_index(self, user_id: UUID) -> str:
    return f"quiz_workflow_attempt_user:{user_id}"

  def _company_user_index(self, company_id: UUID, user_id: UUID) -> str:
    return f"quiz_workflow_attempt_company_user:{company_id}:{user_id}"

  def _company_index(self, company_id: UUID) -> str:
    return f"quiz_workflow_attempt_company:{company_id}"

  def _quiz_index(self, company_id: UUID, quiz_id: UUID) -> str:
    return f"quiz_workflow_attempt_quiz:{company_id}:{quiz_id}"

  # ---------- save ----------

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
    # основний ключ
    attempt_key = self._attempt_key(attempt_id)
    # індекси
    user_index = self._user_index(user_id)
    company_user_index = self._company_user_index(company_id, user_id)
    company_index = self._company_index(company_id)
    quiz_index = self._quiz_index(company_id, quiz_id)
    # структура даних
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
    # потрібно обмежувати розмір індексів, краще використовувати обрізання за score (timestamp)
    timestamp = attempted_at.timestamp()
    cutoff = timestamp - settings.redis_ttl_seconds
    try:
      pipe = self.redis.pipeline(transaction=True)
      # основний payload - зберігаємо повні дані в основному ключі attempt key
      pipe.hset(attempt_key, mapping=payload)
      pipe.expire(attempt_key, settings.redis_ttl_seconds)  # 48 годин
      # secondary indexes
      pipe.zadd(user_index, {str(attempt_id): timestamp})
      pipe.zadd(company_user_index, {str(attempt_id): timestamp})
      pipe.zadd(company_index, {str(attempt_id): timestamp})
      pipe.zadd(quiz_index, {str(attempt_id): timestamp})
      # cleanup old index entries
      pipe.zremrangebyscore(user_index, 0, cutoff)
      pipe.zremrangebyscore(company_user_index, 0, cutoff)
      pipe.zremrangebyscore(company_index, 0, cutoff)
      pipe.zremrangebyscore(quiz_index, 0, cutoff)
      await pipe.execute()
      logger.info(f"Quiz workflow attempt cached (company={company_id}, quiz={quiz_id}, user={user_id}, attempt={attempt_id})")
    except redis.exceptions.RedisError as error:
      logger.error(f"Failed to save quiz attempt in Redis: {error}")

  # ---------- helpers ----------

  async def _fetch_attempts_by_ids(
    self, 
    attempt_ids: list[str]
  ) -> list[dict]:
    if not attempt_ids:
      return []
    pipe = self.redis.pipeline()
    for aid in attempt_ids:
      aid = aid.decode() if isinstance(aid, bytes) else aid
      pipe.hgetall(self._attempt_key(aid))
    raw_results = await pipe.execute()
    attempts = []
    for raw in raw_results:
      if not raw:
        continue
      attempt = {
        key.decode() if isinstance(key, bytes) else key:
        value.decode() if isinstance(value, bytes) else value
        for key, value in raw.items()
      }
      if "answers" in attempt:
        attempt["answers"] = json.loads(attempt["answers"])
      attempts.append(attempt)
    return attempts
  
  # ---------- queries ----------

  async def get_user_attempts(
    self, 
    user_id: UUID
  ) -> list[dict]:
    try:
      attempt_ids = await self.redis.zrange(self._user_index(user_id), 0, -1)
      return await self._fetch_attempts_by_ids(attempt_ids)
    except redis.exceptions.RedisError as error:
      logger.error(f"Redis error fetching user attempts: {error}")
      return []

  async def get_company_user_attempts(
    self, 
    company_id: UUID, 
    user_id: UUID
  ) -> list[dict]:
    try:
      attempt_ids = await self.redis.zrange(self._company_user_index(company_id, user_id), 0, -1)
      return await self._fetch_attempts_by_ids(attempt_ids)
    except redis.exceptions.RedisError as error:
      logger.error(f"Redis error fetching company-user attempts: {error}")
      return []

  async def get_company_attempts(
    self, 
    company_id: UUID
  ) -> list[dict]:
    try:
      attempt_ids = await self.redis.zrange(self._company_index(company_id), 0, -1)
      return await self._fetch_attempts_by_ids(attempt_ids)
    except redis.exceptions.RedisError as error:
      logger.error(f"Redis error fetching company attempts: {error}")
      return []

  async def get_quiz_attempts(
    self, 
    company_id: UUID, 
    quiz_id: UUID
  ) -> list[dict]:
    try:
      attempt_ids = await self.redis.zrange(self._quiz_index(company_id, quiz_id), 0, -1)
      return await self._fetch_attempts_by_ids(attempt_ids)
    except redis.exceptions.RedisError as error:
      logger.error(f"Redis error fetching quiz attempts: {error}")
      return []

  # ---------- delete ----------

  async def delete_attempt(
    self, 
    company_id: UUID,
    quiz_id: UUID,
    user_id: UUID,
    attempt_id: UUID
  ):
    key = self._attempt_key(attempt_id)
    try:
      deleted = await self.redis.delete(key)
      if deleted == 0:
        logger.debug(f"Tried to delete non-existent quiz attempt (user={user_id}, quiz={quiz_id})")
      else:
        logger.debug(f"Deleted quiz attempt from Redis (user={user_id}, quiz={quiz_id})")
    # except Exception as error:
    except redis.exceptions.RedisError as error:
      logger.error(f"Redis error while deleting quiz attempt (user={user_id}, quiz={quiz_id}): {error}")
