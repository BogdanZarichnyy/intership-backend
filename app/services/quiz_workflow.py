from uuid import UUID
from app.core.logger import logger
from app.core.exceptions import QuizNotFound, QuizForbidden
from app.models.user import User
from app.models.quiz import Quiz
from app.models.quiz_workflow import QuizWorkflow
from app.repositories.quiz_workflow import QuizWorkflowRepository
from app.repositories.company_member import CompanyMemberRepository
from app.schemas.quiz_workflow import QuizAttemptRequest, QuizAttemptResponse, UserQuizStatsResponse
from app.services.quiz import QuizService
from app.services.company_member import CompanyMemberService
from app.utils.quiz_workflow_calculator import calculate_quiz_result

class QuizWorkflowService:
  def __init__(self, quiz_workflow_repo: QuizWorkflowRepository, member_repo: CompanyMemberRepository, quiz_service: QuizService, company_member_service: CompanyMemberService):
    self.quiz_workflow_repo = quiz_workflow_repo
    self.member_repo = member_repo
    self.quiz_service = quiz_service
    self.company_member_service = company_member_service

  async def attempt_quiz(
    self,
    company_id: UUID,
    quiz_id: UUID,
    answers: QuizAttemptRequest,
    current_user: User
  ) -> QuizAttemptResponse:
    logger.info(f"User {current_user.id} attempting quiz {quiz_id} in company {company_id}")
    # Перевіряємо, чи користувач є членом компанії, адміном або власником
    await self.member_repo.get_member_of_company(company_id, current_user.id)
    # Отримуємо квіз
    quiz: Quiz = await self.quiz_service.quiz_repo.get_quiz_by_id(quiz_id)
    if not quiz:
      logger.warning(f"Quiz not found quiz_id={quiz_id}")
      raise QuizNotFound()
    if quiz.company_id != company_id:
      logger.warning(f"Quiz {quiz_id} does not belong to company {company_id}")
      raise QuizForbidden("Quiz does not belong to this company")
    # Виклик логіки обрахунку
    result_data = calculate_quiz_result(quiz, answers, current_user.id)
    # Збільшуємо лічильник участі у даному тесті
    await self.quiz_workflow_repo.increment_participation(quiz_id)
    logger.debug(f"Quiz {quiz_id} participation incremented to {quiz.participation_count}")
    # Створюємо запис про результат
    quiz_workflow = QuizWorkflow(
      quiz_id=quiz_id,
      company_id=company_id,
      user_id=current_user.id,
      correct_answers=result_data.correct_answers,
      total_questions=result_data.total_questions,
      score=result_data.score
    )
    # Перевірка на унікальність запису в БД. Наразі в таблиці задіяний UniqueConstraint()
    # existing = await self.quiz_workflow_repo.get_by_user_company_quiz(
    #   user_id=current_user.id,
    #   company_id=company_id,
    #   quiz_id=quiz_id
    # )
    # if existing:
    #   raise QuizForbidden("You have already attempted this quiz")
    result = await self.quiz_workflow_repo.create_quiz_workflow(quiz_workflow)
    logger.info(f"User {current_user.id} attempt recorded successfully for quiz {quiz_id}")
    return QuizAttemptResponse(
      quiz_id=quiz_id,
      company_id=company_id,
      user_id=current_user.id,
      correct_answers=result_data.correct_answers,
      total_questions=result_data.total_questions,
      score=result_data.score,
      attempted_at=result.updated_at  # беремо дату з БД піля додавання quiz_workflow
    )

  async def get_user_stats(
    self, 
    company_id: UUID, 
    user_id: UUID,
    current_user: User
  ) -> UserQuizStatsResponse:
    # Перевіряємо, чи користувач є членом компанії, адміном або власником
    await self.company_member_service.check_owner_or_admin(company_id, current_user.id)
    logger.info(f"Calculating stats for user {user_id} in company {company_id}")
    company_avg = await self.quiz_workflow_repo.get_average_score(user_id, company_id)
    system_avg = await self.quiz_workflow_repo.get_average_score(user_id)
    logger.info(f"User {user_id} stats calculated: company_avg={company_avg:.2f}, system_avg={system_avg:.2f}")
    return UserQuizStatsResponse(
      user_id=user_id,
      company_average_score=company_avg,
      system_average_score=system_avg
    )
