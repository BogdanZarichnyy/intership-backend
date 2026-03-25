from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, update, delete, func
# from sqlalchemy.orm import selectinload, joinedload
from app.models.quiz import Quiz, QuizQuestion, QuizAnswerOption

class QuizRepository:

  def __init__(self, db: AsyncSession):
    self.db = db

  # ==========================
  # CREATE
  # ==========================
  async def create_quiz(
    self,
    quiz_data: dict,
    questions_data: list[dict]
  ) -> UUID:
    query = (
      insert(Quiz)
      .values(**quiz_data)
      .returning(Quiz.id)
    )
    result = await self.db.execute(query)
    quiz_id = result.scalar_one()
    for question in questions_data:
      options = question.pop("options")
      query = (
        insert(QuizQuestion)
        .values(
          quiz_id=quiz_id,
          **question
        )
        .returning(QuizQuestion.id)
      )
      result = await self.db.execute(query)
      question_id = result.scalar_one()
      options_query = insert(QuizAnswerOption).values([
        {
          "question_id": question_id,
          **option
        }
        for option in options
      ])
      await self.db.execute(options_query)
    await self.db.commit()
    return quiz_id

  # ==========================
  # Get Quiz by ID
  # ==========================
  async def get_quiz_by_id(
    self,
    quiz_id: UUID
  ) -> Quiz | None:
    # result = await self.db.execute(
    #   select(Quiz)
    #   .options(
    #     joinedload(Quiz.questions)
    #     .joinedload(QuizQuestion.options)
    #   )
    #   .where(Quiz.id == quiz_id)
    # )
    # return result.unique().scalar_one_or_none()
  
    # Без використання орм метода joinedload() запит виглядатиме так
    # Збираємо join між quiz -> questions -> options
    query = (
      select(
        Quiz,
        QuizQuestion,
        QuizAnswerOption
      )
      .join(QuizQuestion, Quiz.id == QuizQuestion.quiz_id, isouter=True)
      .join(QuizAnswerOption, QuizQuestion.id == QuizAnswerOption.question_id, isouter=True)
      .where(Quiz.id == quiz_id)
    )
    result = await self.db.execute(query)
    rows = result.all()
    if not rows:
      return None
    # Агрегуємо питання та опції під квіз
    quiz_obj = None
    questions_map = {}
    for quiz_row, question_row, option_row in rows:
      if quiz_obj is None:
        quiz_obj = quiz_row
      if question_row:
        q_id = question_row.id
        if q_id not in questions_map:
          questions_map[q_id] = question_row
          questions_map[q_id].options = []
        if option_row:
          questions_map[q_id].options.append(option_row)
    quiz_obj.questions = list(questions_map.values())
    return quiz_obj

  # ==========================
  # Get Quizzes for company
  # ==========================
  async def get_quizzes_for_company(
    self,
    company_id: UUID,
    limit: int,
    offset: int
  ):
    # result = await self.db.execute(
    #   select(Quiz)
    #   .options(
    #     selectinload(Quiz.questions)
    #     .selectinload(QuizQuestion.options)
    #   )
    #   .where(Quiz.company_id == company_id)
    #   .order_by(Quiz.created_at.desc())
    #   .limit(limit)
    #   .offset(offset)
    # )
    # return result.scalars().all()

    # # Без використання орм метода selectinload() запит виглядатиме так
    query = (
      select(
        Quiz,
        QuizQuestion,
        QuizAnswerOption
      )
      .join(QuizQuestion, Quiz.id == QuizQuestion.quiz_id, isouter=True)
      .join(QuizAnswerOption, QuizQuestion.id == QuizAnswerOption.question_id, isouter=True)
      .where(Quiz.company_id == company_id)
      .order_by(Quiz.created_at.desc())
      .limit(limit)
      .offset(offset)
    )
    result = await self.db.execute(query)
    rows = result.all()
    if not rows:
      return []
    # Агрегуємо
    quizzes_map = {}
    questions_map = {}
    for quiz_row, question_row, option_row in rows:
      q_id = quiz_row.id
      if q_id not in quizzes_map:
        quizzes_map[q_id] = quiz_row
        quizzes_map[q_id].questions = []
      if question_row:
        ques_id = question_row.id
        if ques_id not in questions_map:
          questions_map[ques_id] = question_row
          questions_map[ques_id].options = []
          quizzes_map[q_id].questions.append(questions_map[ques_id])
        if option_row:
          questions_map[ques_id].options.append(option_row)
    return list(quizzes_map.values())

  # ==========================
  # Count quizzes
  # ==========================
  async def count_quizzes_for_company(
    self,
    company_id: UUID
  ) -> int:
    result = await self.db.execute(
      select(func.count())
      .select_from(Quiz)
      .where(Quiz.company_id == company_id)
    )
    return result.scalar_one()

  # ==========================
  # UPDATE QUIZ
  # ==========================
  async def update_quiz(
    self,
    quiz_id: UUID,
    quiz_data: dict,
    questions_data: list[dict] | None = None
  ):
    # Оновлюємо сам квіз
    if quiz_data:
      query = update(Quiz).where(Quiz.id == quiz_id).values(**quiz_data)
      await self.db.execute(query)
    # Видаляємо старі питання та опції
    if questions_data is not None:
      # Видаляємо опції
      await self.db.execute(
        delete(QuizAnswerOption).where(
          QuizAnswerOption.question_id.in_(
            select(QuizQuestion.id).where(QuizQuestion.quiz_id == quiz_id)
          )
        )
      )
      # Видаляємо питання
      await self.db.execute(
        delete(QuizQuestion).where(QuizQuestion.quiz_id == quiz_id)
      )
      # Масове вставлення нових питань
      questions_to_insert = [
        {
          "quiz_id": quiz_id,
          "title": question["title"],
          "allows_multiple_correct": question["allows_multiple_correct"]
        } 
        for question in questions_data
      ]
      result = await self.db.execute(
        insert(QuizQuestion).returning(QuizQuestion.id),
        questions_to_insert
      )
      # Правильний спосіб отримати список id в async
      question_ids = [row[0] for row in result.all()]
      # Масове вставлення опцій
      options_to_insert = []
      for q_id, question in zip(question_ids, questions_data):
        for option in question["options"]:
          options_to_insert.append({
            "question_id": q_id,
            "text": option["text"],
            "is_correct": option["is_correct"]
          })
      if options_to_insert:
        await self.db.execute(insert(QuizAnswerOption), options_to_insert)
    await self.db.commit()

  # ==========================
  # DELETE
  # ==========================
  async def delete_quiz(
    self,
    quiz_id: UUID
  ):
    await self.db.execute(delete(Quiz).where(Quiz.id == quiz_id))
    await self.db.commit()

  # =============================
  # Notification scheduler script
  # =============================
  async def get_quizzes_of_company_for_notifications(
    self,
    company_id: UUID
  ) -> list[Quiz]:
    query = (
      select(Quiz)
      .where(Quiz.company_id == company_id)
    )
    result = await self.db.execute(query)
    return result.scalars().all()

  # =============================
  # for Import Excel Quiz
  # =============================
  async def get_by_title_and_company(
    self,
    title: str,
    company_id: UUID
  ) -> Quiz | None:
    result = await self.db.execute(
      select(Quiz)
      .where(
        Quiz.title == title,
        Quiz.company_id == company_id
      )
    )
    return result.scalar_one_or_none()