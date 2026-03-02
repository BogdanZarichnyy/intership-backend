from uuid import UUID
from app.repositories.quiz import QuizRepository
from app.repositories.company import CompanyRepository
from app.models.quiz import Quiz, QuizQuestion, QuizAnswerOption
from app.schemas.quiz import QuizCreateRequest, QuizUpdateRequest
from app.core.exceptions import BusinessError
from app.core.logger import logger
from app.repositories.company_member import CompanyMemberRepository
from app.models.company_member import CompanyRole

class QuizService:
  def __init__(self, quiz_repo: QuizRepository, member_repo: CompanyMemberRepository):
    self.quiz_repo = quiz_repo
    self.member_repo = member_repo

  async def check_owner_or_admin(
    self, 
    company_id: UUID, 
    user_id: UUID
  ):
    # перевіряємо чи користувач є членом компанії
    member = await self.member_repo.get_member(company_id, user_id)
    if not member:
      logger.warning(f"User {user_id} is not a member of company {company_id}")
      raise BusinessError("User is not a member of company")
    # дозволяємо адміну або власнику
    if member.role != CompanyRole.admin:
      company_repo = CompanyRepository(self.member_repo.db)
      company = await company_repo.get_company_by_id(company_id)
      if not company:
        logger.warning(f"Company {company_id} not found during admin check")
        raise BusinessError("Company not found")
      if company.owner_id != user_id:
        logger.warning(f"User {user_id} is neither admin nor owner of company {company_id}")
        raise BusinessError("User must be admin or owner to perform this action")
      logger.warning(f"User {user_id} is neither admin nor owner of company {company_id}")

  async def create_quiz(
    self, 
    company_id: UUID, 
    user_id: UUID, 
    quiz_data: QuizCreateRequest
  ):
    await self.check_owner_or_admin(company_id, user_id)
    if len(quiz_data.questions) < 2:
      raise BusinessError("Quiz must have at least 2 questions")
    questions = []
    for q in quiz_data.questions:
      if not (2 <= len(q.options) <= 4):
        raise BusinessError("Each question must have 2-4 answer options")
      correct_count = sum(1 for o in q.options if o.is_correct)
      if not q.allows_multiple_correct and correct_count != 1:
        raise BusinessError("Question must have exactly one correct answer")
      question = QuizQuestion(title=q.title, allows_multiple_correct=q.allows_multiple_correct)
      question.options = [QuizAnswerOption(text=o.text, is_correct=o.is_correct) for o in q.options]
      questions.append(question)
    quiz = Quiz(company_id=company_id, title=quiz_data.title, description=quiz_data.description, questions=questions)
    quiz = await self.quiz_repo.create_quiz(quiz)
    logger.info(f"Created quiz {quiz.id} for company {company_id}")
    return quiz

  async def record_participation(
    self, 
    quiz_id: UUID
  ):
    """Збільшення лічильника частоти проходження тесту для всіх користувачів"""
    quiz = await self.quiz_repo.get_quiz_by_id(quiz_id)
    if not quiz:
      logger.warning(f"Tried to record participation for non-existent quiz {quiz_id}")
      raise BusinessError("Quiz not found")
    quiz.participation_count += 1
    await self.quiz_repo.update_quiz(quiz)
    logger.info(f"Quiz {quiz_id} participation incremented to {quiz.participation_count}")
    await self.quiz_repo.db.commit()
    return quiz.participation_count # Отримуємо лічильник (число)

  async def get_quizzes(
    self, 
    company_id: UUID, 
    limit: int = 10, 
    offset: int = 0
  ):
    quizzes = await self.quiz_repo.get_quizzes_for_company(company_id, limit, offset)
    total = await self.quiz_repo.count_quizzes_for_company(company_id)
    logger.info(f"Fetched {len(quizzes)} quizzes for company {company_id} (total {total})")
    return {"quizzes": quizzes, "total": total}

  async def get_quiz(
    self, 
    quiz_id: UUID
  ):
    quiz = await self.quiz_repo.get_quiz_by_id(quiz_id)
    if not quiz:
      logger.warning(f"Quiz {quiz_id} not found")
      raise BusinessError("Quiz not found")
    logger.info(f"Fetched quiz {quiz_id} for viewing")
    return quiz

  async def update_quiz(
    self, 
    quiz_id: UUID, 
    user_id: UUID, 
    update_data: QuizUpdateRequest
  ):
    quiz = await self.quiz_repo.get_quiz_by_id(quiz_id)
    if not quiz:
      logger.warning(f"Tried to update non-existent quiz {quiz_id}")
      raise BusinessError("Quiz not found")
    await self.check_owner_or_admin(quiz.company_id, user_id)
    if update_data.title:
      quiz.title = update_data.title
    if update_data.description:
      quiz.description = update_data.description
    if update_data.questions:
      if len(update_data.questions) < 2:
        raise BusinessError("Quiz must have at least 2 questions")
      questions = []
      for q in update_data.questions:
        if not (2 <= len(q.options) <= 4):
          raise BusinessError("Each question must have 2-4 answer options")
        correct_count = sum(1 for o in q.options if o.is_correct)
        if not q.allows_multiple_correct and correct_count != 1:
          raise BusinessError("Question must have exactly one correct answer")
        question = QuizQuestion(title=q.title, allows_multiple_correct=q.allows_multiple_correct)
        question.options = [QuizAnswerOption(text=o.text, is_correct=o.is_correct) for o in q.options]
        questions.append(question)
      quiz.questions = questions
    quiz = await self.quiz_repo.update_quiz(quiz)
    logger.info(f"Updated quiz {quiz.id} for company {quiz.company_id} by user {user_id}")
    await self.quiz_repo.db.commit()
    return quiz

  async def delete_quiz(
    self, 
    quiz_id: UUID, 
    user_id: UUID
  ):
    quiz = await self.quiz_repo.get_quiz_by_id(quiz_id)
    if not quiz:
      logger.warning(f"Tried to delete non-existent quiz {quiz_id}")
      raise BusinessError("Quiz not found")
    await self.check_owner_or_admin(quiz.company_id, user_id)
    await self.quiz_repo.delete_quiz(quiz)
    logger.info(f"Deleted quiz {quiz.id} for company {quiz.company_id} by user {user_id}")
    return
