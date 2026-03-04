from uuid import UUID
from app.repositories.quiz import QuizRepository
from app.repositories.company_member import CompanyMemberRepository
from app.repositories.company import CompanyRepository
from app.models.user import User
from app.models.quiz import Quiz, QuizQuestion, QuizAnswerOption
from app.schemas.quiz import QuizCreateRequest, QuizUpdateRequest
from app.schemas.quiz_dto import quiz_to_schema, quizzes_to_list_schema
from app.schemas.quiz import QuizSchema
from app.core.exceptions import QuizNotFound, QuizForbidden, CompanyMembershipForbidden
from app.models.company_member import CompanyRole
from app.core.logger import logger

class QuizService:
  def __init__(self, quiz_repo: QuizRepository, member_repo: CompanyMemberRepository):
    self.quiz_repo = quiz_repo
    self.member_repo = member_repo

  async def create_quiz(
    self,
    company_id: UUID,
    current_user: User,
    quiz_data: QuizCreateRequest
  ) -> QuizSchema:
    await self.check_owner_or_admin(company_id, current_user.id)
    if len(quiz_data.questions) < 2:
      raise QuizForbidden("Quiz must have at least 2 questions")
    questions: list[QuizQuestion] = []
    for q in quiz_data.questions:
      if not (2 <= len(q.options) <= 4):
        raise QuizForbidden("Each question must have 2-4 answer options")
      correct_count = sum(1 for o in q.options if o.is_correct)
      if not q.allows_multiple_correct and correct_count != 1:
        raise QuizForbidden("Question must have exactly one correct answer")
      question = QuizQuestion(title=q.title, allows_multiple_correct=q.allows_multiple_correct)
      question.options = [QuizAnswerOption(text=o.text, is_correct=o.is_correct) for o in q.options]
      questions.append(question)
    quiz = Quiz(
      company_id=company_id,
      title=quiz_data.title,
      description=quiz_data.description,
      questions=questions
    )
    await self.quiz_repo.add_quiz(quiz)
    await self.quiz_repo.db.commit()
    # Повторно отримуємо quiz з усіма відношеннями
    quiz = await self.quiz_repo.get_quiz_by_id(quiz.id)
    if not quiz:
      logger.info("Failed to fetch created quiz")
      raise QuizNotFound("Failed to fetch created quiz")
    logger.info(f"Created quiz {quiz.id} for company {company_id} by user {current_user.id}")
    return quiz_to_schema(quiz)

  async def get_quizzes(
    self,
    company_id: UUID,
    current_user: User,
    limit: int = 10,
    offset: int = 0
  ) -> dict:
    # Перевіряємо, чи користувач власник або член компанії
    member = await self.member_repo.get_member_of_company(company_id, current_user.id)
    if not member:
      # Якщо не член, перевіряємо чи власник
      company_repo = CompanyRepository(self.member_repo.db)
      company = await company_repo.get_company_by_id(company_id)
      if not company or company.owner_id != current_user.id:
        raise CompanyMembershipForbidden("User must be a company member or owner to view quizzes")
    # Якщо пройшли перевірку — отримуємо квізи
    quizzes = await self.quiz_repo.get_quizzes_for_company(company_id, limit, offset)
    total = await self.quiz_repo.count_quizzes_for_company(company_id)
    return quizzes_to_list_schema(quizzes, total)

  async def get_quiz(
    self,
    quiz_id: UUID,
    current_user: User,
  ) -> QuizSchema:
    # Отримуємо квіз
    quiz = await self.quiz_repo.get_quiz_by_id(quiz_id)
    if not quiz:
      logger.warning(f"Quiz {quiz_id} not found")
      raise QuizNotFound()
    # Перевіряємо права користувача
    member = await self.member_repo.get_member_of_company(quiz.company_id, current_user.id)
    if not member:
      # Якщо не член, перевіряємо чи власник
      company_repo = CompanyRepository(self.member_repo.db)
      company = await company_repo.get_company_by_id(quiz.company_id)
      if not company or company.owner_id != current_user.id:
        logger.warning(f"User {current_user.id} is not allowed to access quiz {quiz_id}")
        raise CompanyMembershipForbidden("User must be a company member or owner to view this quiz")
    logger.info(f"Fetched quiz {quiz_id}")
    return quiz_to_schema(quiz)

  async def update_quiz(
    self,
    quiz_id: UUID,
    current_user: User,
    update_data: QuizUpdateRequest
  ) -> QuizSchema:
    quiz = await self.quiz_repo.get_quiz_by_id(quiz_id)
    if not quiz:
      logger.warning(f"Tried to update non-existent quiz {quiz_id}")
      raise QuizNotFound()
    await self.check_owner_or_admin(quiz.company_id, current_user.id)
    if update_data.title:
      quiz.title = update_data.title
    if update_data.description:
      quiz.description = update_data.description
    if update_data.questions:
      if len(update_data.questions) < 2:
        raise QuizForbidden("Quiz must have at least 2 questions")
      # Видаляємо старі питання та варіанти
      await self.quiz_repo.delete_questions_for_quiz(quiz.id)
      questions: list[QuizQuestion] = []
      for q in update_data.questions:
        if not (2 <= len(q.options) <= 4):
          raise QuizForbidden("Each question must have 2-4 answer options")
        correct_count = sum(1 for o in q.options if o.is_correct)
        if not q.allows_multiple_correct and correct_count != 1:
          raise QuizForbidden("Question must have exactly one correct answer")
        question = QuizQuestion(title=q.title, allows_multiple_correct=q.allows_multiple_correct)
        question.options = [QuizAnswerOption(text=o.text, is_correct=o.is_correct) for o in q.options]
        questions.append(question)
      quiz.questions = questions
    await self.quiz_repo.db.commit()
    # Повторно отримуємо quiz з усіма відношеннями
    quiz = await self.quiz_repo.get_quiz_by_id(quiz.id)
    if not quiz:
      logger.info("Failed to fetch created quiz")
      raise QuizNotFound("Failed to fetch updated quiz")
    logger.info(f"Updated quiz {quiz.id} for company {quiz.company_id} by user {current_user.id}")
    return quiz_to_schema(quiz)

  async def delete_quiz(
    self,
    quiz_id: UUID,
    current_user: User
  ) -> None:
    # Отримуємо квіз
    quiz = await self.quiz_repo.get_quiz_by_id(quiz_id)
    if not quiz:
      logger.warning(f"Tried to delete non-existent quiz {quiz_id}")
      raise QuizNotFound()
    # Перевірка доступу: власник або адмін компанії
    member = await self.member_repo.get_member_of_company(quiz.company_id, current_user.id)
    if member and member.role == CompanyRole.admin:
      logger.info(f"User {current_user.id} is an admin of company {quiz.company_id}")
    else:
      company_repo = CompanyRepository(self.member_repo.db)
      company = await company_repo.get_company_by_id(quiz.company_id)
      if not company or company.owner_id != current_user.id:
        logger.warning(f"User {current_user.id} is not allowed to delete quiz {quiz_id}")
        raise CompanyMembershipForbidden("User must be an admin or owner to delete this quiz")
      logger.info(f"User {current_user.id} is the owner of company {quiz.company_id}")
    # Видалення квіза
    await self.quiz_repo.delete(quiz)
    await self.quiz_repo.db.commit()
    logger.info(f"Deleted quiz {quiz.id} for company {quiz.company_id} by user {current_user.id}")

  async def check_owner_or_admin(
    self,
    company_id: UUID,
    user_id: UUID
  ) -> None:
    member = await self.member_repo.get_member_of_company(company_id, user_id)
    if not member or member.role != CompanyRole.admin:
      company_repo = CompanyRepository(self.member_repo.db)
      company = await company_repo.get_company_by_id(company_id)
      if not company:
        logger.warning(f"Company {company_id} not found during owner/admin check")
        raise QuizNotFound()
      if not company or company.owner_id != user_id:
        logger.warning(f"User {user_id} is neither admin nor owner of company {company_id}")
        raise CompanyMembershipForbidden("User must be admin or owner to perform this action")
      logger.info(f"User {user_id} is company owner of {company_id}")
      return
    logger.info(f"User {user_id} passed owner/admin check for company {company_id}")

  # Збільшення лічильника частоти проходження тесту для всіх користувачів
  async def record_participation(
    self, 
    quiz_id: UUID
  ):
    quiz = await self.quiz_repo.get_quiz_by_id(quiz_id)
    if not quiz:
      logger.warning(f"Tried to record participation for non-existent quiz {quiz_id}")
      raise QuizNotFound()
    quiz.participation_count += 1
    await self.quiz_repo.update_quiz(quiz)
    logger.info(f"Quiz {quiz_id} participation incremented to {quiz.participation_count}")
    await self.quiz_repo.db.commit()
    return quiz.participation_count # Отримуємо лічильник активності (число)
