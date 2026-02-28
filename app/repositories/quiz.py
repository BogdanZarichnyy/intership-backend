from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from uuid import UUID
from app.models.quiz import Quiz, QuizQuestion, QuizAnswerOption

class QuizRepository:
  def __init__(self, db: AsyncSession):
    self.db = db

  async def create_quiz(
    self, 
    quiz: Quiz
  ):
    self.db.add(quiz)
    await self.db.commit()
    await self.db.refresh(quiz)
    return quiz

  async def get_quiz_by_id(
    self, 
    quiz_id: UUID
  ) -> Quiz | None:
    result = await self.db.execute(select(Quiz)
      .where(Quiz.id == quiz_id))
    return result.scalar_one_or_none()

  async def get_quizzes_for_company(
    self, 
    company_id: UUID, 
    limit: int, 
    offset: int
  ):
    result = await self.db.execute(
      select(Quiz)
      .where(Quiz.company_id == company_id)
      .order_by(Quiz.created_at.desc())
      .limit(limit)
      .offset(offset)
    )
    return result.scalars().all()

  async def count_quizzes_for_company(
    self, 
    company_id: UUID
  ):
    result = await self.db.execute(select(func.count())
      .select_from(Quiz)
      .where(Quiz.company_id == company_id))
    return result.scalar_one()

  async def update_quiz(
    self, 
    quiz: Quiz
  ):
    await self.db.commit()
    await self.db.refresh(quiz)
    return quiz

  async def delete_quiz(
    self, 
    quiz: Quiz
  ):
    await self.db.delete(quiz)
    await self.db.commit()
