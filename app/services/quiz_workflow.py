from uuid import UUID
from app.repositories.quiz_workflow import QuizWorkflowRepository
from app.services.quiz import QuizService
from app.models.user import User
from app.models.quiz import Quiz, QuizQuestion, QuizAnswerOption
from app.models.quiz_workflow import QuizWorkflow
from app.schemas.quiz_workflow import QuizAttemptRequest, QuizAttemptResponse, UserQuizStatsResponse
from app.core.exceptions import QuizNotFound, QuizForbidden
from app.core.logger import logger

class QuizWorkflowService:
  def __init__(self, result_repo: QuizWorkflowRepository, quiz_service: QuizService):
    self.result_repo = result_repo
    self.quiz_service = quiz_service

  async def attempt_quiz(
    self,
    company_id: UUID,
    quiz_id: UUID,
    answers: QuizAttemptRequest,
    current_user: User
  ) -> QuizAttemptResponse:
    logger.info(f"User {current_user.id} attempting quiz {quiz_id} in company {company_id}")
    # 1. Перевіряємо, чи користувач є членом компанії, адміном або власником
    await self.quiz_service.check_owner_or_admin(company_id, current_user.id)
    # 2. Отримуємо тест
    quiz: Quiz = await self.quiz_service.quiz_repo.get_quiz_by_id(quiz_id)
    if not quiz:
      logger.warning(f"Quiz not found quiz_id={quiz_id}")
      raise QuizNotFound()
    if quiz.company_id != company_id:
      logger.warning(f"Quiz {quiz_id} does not belong to company {company_id}")
      raise QuizForbidden("Quiz does not belong to this company")
    questions: list[QuizQuestion] = list(quiz.questions)  # сувора типізація
    # Створюємо мапу питань для швидкого доступу
    question_map: dict[UUID, QuizQuestion] = {question.id: question for question in questions}
    # 3. Валідація вхідних даних (payload)
    submitted_question_ids: list[UUID] = [answer.question_id for answer in answers.answers]
    submitted_question_set: set[UUID] = set(submitted_question_ids)
    quiz_question_set: set[UUID] = set(question_map.keys())
    logger.debug(f"User {current_user.id} submitted {len(submitted_question_ids)} answers")
    # 3.1 Duplicate question IDs
    if len(submitted_question_ids) != len(submitted_question_set):
      logger.warning(f"Duplicate question IDs detected (user={current_user.id}, quiz={quiz_id})")
      raise QuizForbidden("Duplicate question IDs in submission")
    # 3.2 Foreign question IDs
    extra_questions = submitted_question_set - quiz_question_set
    if extra_questions:
      logger.warning(f"Invalid question IDs {extra_questions} (user={current_user.id}, quiz={quiz_id})")
      raise QuizForbidden("Submission contains questions not belonging to this quiz")
    # 3.3 Missing questions
    if submitted_question_set != quiz_question_set:
      missing = quiz_question_set - submitted_question_set
      logger.warning(f"Incomplete submission. Missing: {missing} (user={current_user.id}, quiz={quiz_id})")
      raise QuizForbidden("All quiz questions must be answered")
    logger.debug(f"Question-level validation passed (user={current_user.id}, quiz={quiz_id})")
    # 4. Підрахунок результатів
    total_questions = len(questions)
    correct_answers = 0
    for answer in answers.answers:
      question = question_map.get(answer.question_id)
      answers: list[QuizAnswerOption] = list(question.options)  # сувора типізація
      valid_option_ids: set[UUID] = {option.id for option in answers}
      selected_option_ids: list[UUID] = answer.selected_option_ids
      selected_option_set: set[UUID] = set(selected_option_ids)
      # 4.1 Duplicate option IDs
      if len(selected_option_ids) != len(selected_option_set):
        logger.warning(f"Duplicate option IDs in question {question.id} (user={current_user.id})")
        raise QuizForbidden("Duplicate answer options detected")
      # 4.2 Foreign option IDs
      invalid_options = selected_option_set - valid_option_ids
      if invalid_options:
        logger.warning(f"Invalid option IDs {invalid_options} for question {question.id} (user={current_user.id})")
        raise QuizForbidden("Answer contains options not belonging to this question")
      correct_option_ids: set[UUID] = {option.id for option in answers if option.is_correct}
      if selected_option_set == correct_option_ids:
        correct_answers += 1
        logger.debug(f"Question {question.id} answered correctly by user {current_user.id}")
      else:
        logger.debug(f"Question {question.id} answered incorrectly by user {current_user.id}")
    score = correct_answers / total_questions if total_questions else 0.0
    logger.info(f"User {current_user.id} scored {score:.2f} on quiz {quiz_id}")
    # 5. Збільшуємо лічильник участі у даному тесті
    quiz.participation_count += 1
    await self.quiz_service.quiz_repo.update_quiz(quiz)
    logger.debug(f"Quiz {quiz_id} participation incremented to {quiz.participation_count}")
    # Створюємо запис про результат
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
    logger.debug(f"Result record created for user {current_user.id} on quiz {quiz_id}")
    # Оновлюємо об’єкт після коміту
    await self.result_repo.db.refresh(result)
    logger.info(f"User {current_user.id} attempt recorded successfully for quiz {quiz_id}")
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
