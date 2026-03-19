from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, update, delete, func, case
from app.models.quiz import Quiz, QuizQuestion, QuizAnswerOption
from app.models.quiz_workflow import QuizWorkflow

class QuizWorkflowRepository:
  def __init__(self, db: AsyncSession):
    self.db = db

  async def create_quiz_workflow(
    self, 
    quiz_workflow: QuizWorkflow
  ) -> QuizWorkflow:
    query = (
      insert(QuizWorkflow)
      .values(
        user_id=quiz_workflow.user_id,
        company_id=quiz_workflow.company_id,
        quiz_id=quiz_workflow.quiz_id,
        correct_answers=quiz_workflow.correct_answers,
        total_questions=quiz_workflow.total_questions,
        score=quiz_workflow.score
      )
      .returning(QuizWorkflow)
    )
    result = await self.db.execute(query)
    await self.db.commit()
    return result.scalar_one()
  
  # Перевірка на унікальність запису в БД. Наразі в таблиці задіяний UniqueConstraint()
  # async def get_by_user_company_quiz(
  #   self, 
  #   user_id: UUID, 
  #   company_id: UUID, 
  #   quiz_id: UUID
  # ) -> QuizWorkflow | None:
  #   result = await self.db.execute(
  #     select(QuizWorkflow).where(
  #       QuizWorkflow.user_id == user_id,
  #       QuizWorkflow.company_id == company_id,
  #       QuizWorkflow.quiz_id == quiz_id
  #     )
  #   )
  #   return result.scalar_one_or_none()

  # =====================================
  # Increment participation count in Quiz
  # =====================================
  async def increment_participation(
    self, 
    quiz_id: UUID
  ):
    await self.db.execute(
      update(Quiz)
      .where(Quiz.id == quiz_id)
      .values(participation_count=Quiz.participation_count + 1)
    )
    await self.db.commit()

  # =============================
  # Get user results
  # =============================
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
  
  # =============================
  # Get calculate correct answers
  # =============================
  async def calculate_correct_answers(
    self,
    quiz_id: UUID,
    submitted_answers: dict[UUID, set[UUID]]
  ) -> int:
    # формуємо список усіх переданих option_id
    submitted_option_ids = [
      option_id
      for option_set in submitted_answers.values()
      for option_id in option_set
    ]
    query = (
      select(
        QuizAnswerOption.question_id,
        func.count(
          case((QuizAnswerOption.is_correct == True, 1))
        ).label("correct_count"),
        func.count(
          case((QuizAnswerOption.id.in_(submitted_option_ids), 1))
        ).label("selected_count")
      )
      .join(QuizQuestion, QuizQuestion.id == QuizAnswerOption.question_id)
      .where(QuizQuestion.quiz_id == quiz_id)
      .group_by(QuizAnswerOption.question_id)
    )
    result = await self.db.execute(query)
    rows = result.all()
    correct_answers = 0
    for row in rows:
      question_id = row.question_id
      submitted = submitted_answers.get(question_id, set())
      if row.correct_count == len(submitted) and row.selected_count == len(submitted):
        correct_answers += 1
    return correct_answers

  # ==========================
  # INSERT result
  # ==========================
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

  # =============================
  # Delete all results for quiz
  # =============================
  async def delete_by_quiz_id(
    self,
    quiz_id: UUID
  ) -> None:
    query = (
      delete(QuizWorkflow)
      .where(QuizWorkflow.quiz_id == quiz_id)
    )
    await self.db.execute(query)
    await self.db.commit()

  # =======================================
  # Get company workflows for notifications
  # =======================================
  async def get_company_workflows(
    self, 
    company_id: UUID
  ):
    query = (
      select(QuizWorkflow)
      .where(QuizWorkflow.company_id == company_id)
    )
    result = await self.db.execute(query)
    return result.scalars().all()
