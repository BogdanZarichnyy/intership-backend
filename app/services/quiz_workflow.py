from uuid import UUID
from app.repositories.quiz_workflow import QuizWorkflowRepository
from app.services.quiz import QuizService
from app.models.user import User
from app.models.quiz import Quiz, QuizQuestion, QuizAnswerOption
from app.models.quiz_workflow import QuizWorkflow
from app.schemas.quiz_workflow import QuizAttemptRequest, QuizAttemptResponse, UserQuizStatsResponse
from app.core.exceptions import QuizNotFound, QuizForbidden
from app.core.logger import logger
from app.services.quiz_attempt_cache import QuizAttemptCacheService

class QuizWorkflowService:
  def __init__(self, result_repo: QuizWorkflowRepository, quiz_service: QuizService):
    self.result_repo = result_repo
    self.quiz_service = quiz_service

  async def attempt_quiz(
    self,
    company_id: UUID,
    quiz_id: UUID,
    payload: QuizAttemptRequest,
    current_user: User
  ) -> QuizAttemptResponse:
    logger.info(f"User {current_user.id} attempting quiz {quiz_id} in company {company_id}")
    # Перевірка прав
    await self.quiz_service.check_owner_or_admin(company_id, current_user.id)
    # Отримуємо тест
    quiz: Quiz = await self.quiz_service.quiz_repo.get_quiz_by_id(quiz_id)
    if not quiz:
      logger.warning(f"Quiz not found quiz_id={quiz_id}")
      raise QuizNotFound()
    if quiz.company_id != company_id:
      logger.warning(f"Quiz {quiz_id} does not belong to company {company_id}")
      raise QuizForbidden("Quiz does not belong to this company")
    questions: list[QuizQuestion] = list(quiz.questions)
    question_map = {question.id: question for question in questions}
    submitted_ids = [answer.question_id for answer in payload.answers]
    if len(submitted_ids) != len(set(submitted_ids)):
      raise QuizForbidden("Duplicate question IDs in submission")
    extra = set(submitted_ids) - set(question_map.keys())
    if extra:
      raise QuizForbidden("Submission contains questions not belonging to this quiz")
    missing = set(question_map.keys()) - set(submitted_ids)
    if missing:
      raise QuizForbidden("All quiz questions must be answered")
    # Підрахунок результатів
    correct_answers = 0
    for answer in payload.answers:
      options: list[QuizAnswerOption] = list(question_map[answer.question_id].options)
      selected_set = set(answer.selected_option_ids)
      if len(answer.selected_option_ids) != len(selected_set):
        raise QuizForbidden("Duplicate answer options detected")
      invalid = selected_set - {option.id for option in options}
      if invalid:
        raise QuizForbidden("Answer contains options not belonging to this question")
      correct_ids = {option.id for option in options if option.is_correct}
      if selected_set == correct_ids:
        correct_answers += 1
    total_questions = len(questions)
    score = correct_answers / total_questions if total_questions else 0.0
    quiz.participation_count += 1
    await self.quiz_service.quiz_repo.update_quiz(quiz)
    # Зберігаємо результат у БД
    result = QuizWorkflow(
      user_id=current_user.id,
      company_id=company_id,
      quiz_id=quiz_id,
      correct_answers=correct_answers,
      total_questions=total_questions,
      score=score,
    )
    self.result_repo.db.add(result)
    await self.result_repo.db.commit()
    await self.result_repo.db.refresh(result)
    # Підготовка до Redis (UUID -> str)
    answers_for_cache = []
    for a in payload.answers:
      question = question_map[a.question_id]
      answers: list[QuizAnswerOption] = list(question.options)
      # Створюємо список опцій для Redis
      selected_options = []
      for option_id in a.selected_option_ids:
        # Знаходимо відповідний об'єкт варіанту у питанні
        option_obj = next((option for option in answers if option.id == option_id), None)
        if option_obj is None:
          raise QuizForbidden("Selected option does not exist in the question")
        selected_options.append({
          "answer": str(option_id),
          "is_correct": option_obj.is_correct  # реальна правильність опції
        })
      answers_for_cache.append({
        "question_id": str(a.question_id),
        "selected_option_ids": selected_options
      })
    cache_service = QuizAttemptCacheService()
    await cache_service.save_attempt(
      attempt_id=str(result.id),
      user_id=str(current_user.id),
      company_id=str(company_id),
      quiz_id=str(quiz_id),
      answers=answers_for_cache,
      total_questions=total_questions,
      correct_answers=correct_answers,
      score=score
    )
    return QuizAttemptResponse(
      quiz_id=quiz_id,
      user_id=current_user.id,
      correct_answers=correct_answers,
      total_questions=total_questions,
      score=score,
      attempted_at=result.updated_at
    )

  async def get_user_stats(
    self, 
    company_id: UUID, 
    user_id: UUID,
    current_user: User
  ) -> UserQuizStatsResponse:
    # Перевіряємо, чи користувач є членом компанії, адміном або власником
    await self.quiz_service.check_owner_or_admin(company_id, current_user.id)
    logger.info(f"Calculating stats for user {user_id} in company {company_id}")
    company_avg = await self.result_repo.get_average_score(user_id, company_id)
    system_avg = await self.result_repo.get_average_score(user_id)
    logger.info(f"User {user_id} stats calculated: company_avg={company_avg:.2f}, system_avg={system_avg:.2f}")
    return UserQuizStatsResponse(
      user_id=user_id,
      company_average_score=company_avg,
      system_average_score=system_avg
    )
