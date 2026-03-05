from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.quiz_workflow import QuizWorkflow

class QuizWorkflowRepository:
  def __init__(self, db: AsyncSession):
    self.db = db

  async def create_result(
    self, 
    result: QuizWorkflow
  ) -> QuizWorkflow:
    self.db.add(result)
    await self.db.commit()
    await self.db.refresh(result)
    return result

  async def get_user_results(
    self, 
    user_id: UUID, 
    company_id: UUID | None = None
  ) -> list[QuizWorkflow]:
    query = select(QuizWorkflow).where(QuizWorkflow.user_id == user_id)
    if company_id is not None:
      query = query.where(QuizWorkflow.company_id == company_id)
    result = await self.db.execute(query)
    return result.scalars().all()

  async def get_users_results(
    self, 
    company_id: UUID
  ) -> list[QuizWorkflow]:
    query = select(QuizWorkflow).where(QuizWorkflow.company_id == company_id)
    result = await self.db.execute(query)
    return result.scalars().all()

  async def get_average_score(
    self, 
    user_id: UUID, 
    company_id: UUID | None = None
  ) -> float:
    query = select(
      func.coalesce(func.sum(QuizWorkflow.correct_answers), 0),
      func.coalesce(func.sum(QuizWorkflow.total_questions), 0)
    ).where(QuizWorkflow.user_id == user_id)
    if company_id is not None:
      query = query.where(QuizWorkflow.company_id == company_id)
    res = await self.db.execute(query)
    correct_sum, total_sum = res.one()
    return float(correct_sum) / float(total_sum) if total_sum else 0.0
