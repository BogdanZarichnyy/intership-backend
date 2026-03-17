from uuid import UUID
from app.core.logger import logger
from app.core.exceptions import QuizNotFound, QuizForbidden, CompanyMembershipForbidden, CompanyNotFound
from app.models.user import User
from app.repositories.quiz import QuizRepository
from app.repositories.company_member import CompanyMemberRepository
from app.repositories.company import CompanyRepository
from app.schemas.quiz import QuizSchema, QuizCreateRequest, QuizUpdateRequest
from app.schemas.quiz_dto import quiz_to_schema, quizzes_to_list_schema
from app.services.company_member import CompanyMemberService

class QuizService:
  def __init__(
    self,
    quiz_repo: QuizRepository,
    member_repo: CompanyMemberRepository,
    company_repo: CompanyRepository,
    company_member_service: CompanyMemberService
  ):
    self.quiz_repo = quiz_repo
    self.member_repo = member_repo
    self.company_repo = company_repo
    self.company_member_service = company_member_service

  # ================================
  # Створення нового квізу
  # ================================
  async def create_quiz(
    self,
    company_id: UUID,
    current_user: User,
    quiz_data: QuizCreateRequest
  ) -> QuizSchema:
    company = await self.company_repo.get_company_by_id(company_id)
    if not company:
      logger.warning(f"Company not found company_id={company_id}")
      raise CompanyNotFound()
    await self.company_member_service.check_owner_or_admin(company_id, current_user.id)
    # Валідація через Pydantic
    quiz_data.model_validate(quiz_data)
    # Перевірка бізнес-логіки: мінімум 2 питання
    if len(quiz_data.questions) < 2:
      raise QuizForbidden("Quiz must have at least 2 questions")
    # Перевірка питань і опцій
    questions_data = []
    for question in quiz_data.questions:
      if not (2 <= len(question.options) <= 4):
        raise QuizForbidden("Each question must have 2-4 answer options")
      correct_count = sum(1 for option in question.options if option.is_correct)
      if not question.allows_multiple_correct and correct_count != 1:
        raise QuizForbidden("Question must have exactly one correct answer")
      questions_data.append(question.model_dump())
    quiz_dict = quiz_data.model_dump(exclude={"questions"})
    quiz_dict["company_id"] = company_id
    quiz_id: UUID = await self.quiz_repo.create_quiz(
      quiz_dict,
      questions_data
    )
    # Повторно отримуємо quiz з усіма відношеннями
    quiz = await self.quiz_repo.get_quiz_by_id(quiz_id)
    if not quiz:
      logger.info("Failed to fetch created quiz")
      raise QuizNotFound()
    logger.info(f"Created quiz {quiz.id} for company {company_id} by user {current_user.id}")
    return quiz_to_schema(quiz)

  # ================================
  # Отримання списку квізів компанії
  # ================================
  async def get_quizzes(
    self,
    company_id: UUID,
    current_user: User,
    limit: int = 10,
    offset: int = 0
  ) -> dict:
    company = await self.company_repo.get_company_by_id(company_id)
    if not company:
      logger.warning(f"Company not found company_id={company_id}")
      raise CompanyNotFound()
    # Перевіряємо, чи користувач являється членом компанії
    member = await self.member_repo.get_member_of_company(company_id, current_user.id)
    # Якщо не член, перевіряємо чи власник
    if not member and company.owner_id != current_user.id:
      logger.warning(f"User user_id={current_user.id} must be a company member or owner to view quizzes company_id={company_id}")
      raise CompanyMembershipForbidden("User must be a company member or owner to view quizzes")
    # Якщо пройшли перевірку — отримуємо квізи
    quizzes = await self.quiz_repo.get_quizzes_for_company(company_id, limit, offset)
    total = await self.quiz_repo.count_quizzes_for_company(company_id)
    return quizzes_to_list_schema(quizzes, total)

  # ================================
  # Отримання одного квізу
  # ================================
  async def get_quiz(
    self,
    company_id: UUID,
    quiz_id: UUID,
    current_user: User,
  ) -> QuizSchema:
    company = await self.company_repo.get_company_by_id(company_id)
    if not company:
      logger.warning(f"Company not found company_id={company_id}")
      raise CompanyNotFound()
    # Перевіряємо, чи користувач являється членом компанії
    member = await self.member_repo.get_member_of_company(company_id, current_user.id)
    # Якщо не член, перевіряємо чи власник
    if not member and company.owner_id != current_user.id:
      logger.warning(f"User {current_user.id} is not allowed to access quiz {quiz_id}")
      raise CompanyMembershipForbidden("User must be a company member or owner to view this quiz")
    # Отримуємо квіз
    quiz = await self.quiz_repo.get_quiz_by_id(quiz_id)
    if not quiz:
      logger.warning(f"Quiz {quiz_id} not found")
      raise QuizNotFound()
    logger.info(f"Fetched quiz {quiz_id}")
    return quiz_to_schema(quiz)

  # ================================
  # Оновлення квізу
  # ================================
  async def update_quiz(
    self,
    company_id: UUID,
    quiz_id: UUID,
    current_user: User,
    update_data: QuizUpdateRequest
  ) -> QuizSchema:
    await self.company_member_service.check_owner_or_admin(company_id, current_user.id)
    quiz = await self.quiz_repo.get_quiz_by_id(quiz_id)
    if not quiz:
      logger.warning(f"Tried to update non-existent quiz {quiz_id}")
      raise QuizNotFound()
    data = update_data.model_dump(exclude_unset=True)
    questions_data = None
    if "questions" in data:
      questions = data.pop("questions")
      if len(questions) < 2:
        raise QuizForbidden("Quiz must have at least 2 questions")
      # Видаляємо старі питання та варіанти
      questions_data = []
      for question in questions:
        if not (2 <= len(question["options"]) <= 4):
          raise QuizForbidden("Each question must have 2-4 answer options")
        correct_count = sum(1 for option in question["options"] if option["is_correct"])
        if not question["allows_multiple_correct"] and correct_count != 1:
          raise QuizForbidden("Question must have exactly one correct answer")
        questions_data.append(question)
    await self.quiz_repo.update_quiz(quiz_id, data, questions_data)
    # Повторно отримуємо quiz з усіма відношеннями
    quiz = await self.quiz_repo.get_quiz_by_id(quiz.id)
    if not quiz:
      logger.info("Failed to fetch created quiz")
      raise QuizNotFound()
    logger.info(f"Updated quiz {quiz.id} for company {quiz.company_id} by user {current_user.id}")
    return quiz_to_schema(quiz)

  # ================================
  # Видалення квізу
  # ================================
  async def delete_quiz(
    self,
    company_id: UUID,
    quiz_id: UUID,
    current_user: User
  ) -> None:
    # Перевірка доступу: власник або адмін компанії
    await self.company_member_service.check_owner_or_admin(company_id, current_user.id)
    # Отримуємо квіз
    quiz = await self.quiz_repo.get_quiz_by_id(quiz_id)
    if not quiz:
      logger.warning(f"Tried to delete non-existent quiz {quiz_id}")
      raise QuizNotFound()
    # Видалення квіза
    await self.quiz_repo.delete_quiz(quiz_id)
    logger.info(f"Deleted quiz {quiz_id} for company {quiz.company_id} by user {current_user.id}")
