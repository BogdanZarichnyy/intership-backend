from uuid import UUID
from app.repositories.quiz_result import QuizResultRepository
from app.services.quiz import QuizService
from app.models.quiz_result import QuizResult
from app.models.user import User
from app.schemas.quiz_result import QuizAttemptRequest, QuizAttemptResponse, UserQuizStatsResponse
from app.core.exceptions import BusinessError
from app.core.logger import logger
from datetime import datetime, timezone

class QuizResultService:
  def __init__(self, result_repo: QuizResultRepository, quiz_service: QuizService):
    self.result_repo = result_repo
    self.quiz_service = quiz_service

  async def attempt_quiz(
    self,
    company_id: UUID,
    quiz_id: UUID,
    current_user: User,
    answers: QuizAttemptRequest
  ) -> QuizAttemptResponse:
    # Отримуємо тест
    quiz = await self.quiz_service.get_quiz(quiz_id)
    if not quiz:
      logger.warning(f"Quiz not found quiz_id={quiz_id}")
      raise BusinessError("Quiz not found")
    if quiz.company_id != company_id:
      logger.warning(f"Quiz {quiz_id} does not belong to company {company_id}")
      raise BusinessError("Quiz does not belong to this company")
    total_questions = len(quiz.questions)
    correct_answers = 0
    # Створюємо мапу питань для швидкого доступу
    question_map = {q.id: q for q in quiz.questions}
    for answer in answers.answers:
      question = question_map.get(answer.question_id)
      if not question:
        logger.warning(f"Answer provided for non-existent question {answer.question_id}")
        continue
      correct_option_ids = {o.id for o in question.options if o.is_correct}
      if set(answer.selected_option_ids) == correct_option_ids:
        correct_answers += 1
        logger.debug(f"Question {question.id} answered correctly by user {current_user.id}")
      else:
        logger.debug(f"Question {question.id} answered incorrectly by user {current_user.id}")
    score = correct_answers / total_questions if total_questions else 0.0
    logger.info(f"User {current_user.id} scored {score:.2f} on quiz {quiz_id}")
    # Виконуємо оновлення участі та створення результату в одній транзакції
    async with self.result_repo.db.begin():  # початок транзакції
      # 1. Збільшуємо лічильник участі
      quiz.participation_count += 1
      await self.quiz_service.quiz_repo.update_quiz(quiz)
      logger.debug(f"Quiz {quiz_id} participation incremented to {quiz.participation_count}")
      # 2. Створюємо запис про результат
      result = QuizResult(
        user_id=current_user.id,
        company_id=company_id,
        quiz_id=quiz_id,
        correct_answers=correct_answers,
        total_questions=total_questions,
        score=score,
        updated_at=datetime.now(timezone.utc)  # використовуємо updated_at як час останньої спроби
      )
      self.result_repo.db.add(result)
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
    user_id: UUID
  ) -> UserQuizStatsResponse:
    logger.info(f"Calculating stats for user {user_id} in company {company_id}")
    company_avg = await self.result_repo.get_average_score(user_id, company_id)
    system_avg = await self.result_repo.get_average_score(user_id)
    logger.info(f"User {user_id} stats calculated: company_avg={company_avg:.2f}, system_avg={system_avg:.2f}")
    return UserQuizStatsResponse(
      user_id=user_id,
      company_average_score=company_avg,
      system_average_score=system_avg
    )
