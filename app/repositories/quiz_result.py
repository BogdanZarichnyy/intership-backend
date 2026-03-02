from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.quiz_result import QuizResult

class QuizResultRepository:
  def __init__(self, db: AsyncSession):
    self.db = db

  async def create_result(
    self, 
    result: QuizResult
  ) -> QuizResult:
    self.db.add(result)
    await self.db.commit()
    await self.db.refresh(result)
    return result

  async def get_user_results(
    self, 
    user_id: UUID, 
    company_id: UUID | None = None
  ):
    query = select(QuizResult).where(QuizResult.user_id == user_id)
    if company_id is not None:
      query = query.where(QuizResult.company_id == company_id)
    result = await self.db.execute(query)
    return result.scalars().all()

  async def get_average_score(
    self, 
    user_id: UUID, 
    company_id: UUID | None = None
  ) -> float:
    query = select(
      func.coalesce(func.sum(QuizResult.correct_answers), 0),
      func.coalesce(func.sum(QuizResult.total_questions), 0)
    ).where(QuizResult.user_id == user_id)
    if company_id is not None:
      query = query.where(QuizResult.company_id == company_id)
    res = await self.db.execute(query)
    correct_sum, total_sum = res.one()
    return float(correct_sum) / float(total_sum) if total_sum else 0.0
