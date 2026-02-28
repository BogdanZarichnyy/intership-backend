from uuid import UUID

from app.repositories.quiz_result import QuizResultRepository
from app.schemas.quiz_result import QuizAttemptRequest, QuizAttemptResponse, UserQuizStatsResponse
from app.services.quiz import QuizService
from app.models.quiz_result import QuizResult
from app.core.exceptions import BusinessError
from app.core.logger import logger

class QuizResultService:
  def __init__(self, result_repo: QuizResultRepository, quiz_service: QuizService):
    self.result_repo = result_repo
    self.quiz_service = quiz_service

  async def attempt_quiz(
    self, 
    quiz_id: UUID, 
    user_id: UUID, 
    company_id: UUID, 
    answers: QuizAttemptRequest
  ) -> QuizAttemptResponse:
    quiz = await self.quiz_service.get_quiz(quiz_id)
    if not quiz:
      raise BusinessError("Quiz not found")
    # Збільшуємо лічильник участі перед обчисленням результатів
    await self.quiz_service.record_participation(quiz_id)  # або виклик через сервіс, якщо він там є
    total_questions = len(quiz.questions)
    correct_answers = 0
    # перевірка відповідей
    question_map = {q.id: q for q in quiz.questions}
    for answer in answers.answers:
      question = question_map.get(answer.question_id)
      if not question:
        continue
      correct_option_ids = {o.id for o in question.options if o.is_correct}
      if set(answer.selected_option_ids) == correct_option_ids:
        correct_answers += 1
    score = correct_answers / total_questions if total_questions else 0.0
    result = QuizResult(
      user_id=user_id,
      company_id=company_id,
      quiz_id=quiz_id,
      correct_answers=correct_answers,
      total_questions=total_questions,
      score=score
    )
    result = await self.result_repo.create_result(result)
    logger.info(f"User {user_id} attempted quiz {quiz_id} with score {score:.2f}")
    return QuizAttemptResponse(
      quiz_id=quiz_id,
      user_id=user_id,
      correct_answers=correct_answers,
      total_questions=total_questions,
      score=score,
      attempted_at=result.created_at
    )

  async def get_user_stats(
    self, 
    user_id: UUID, 
    company_id: UUID
  ) -> UserQuizStatsResponse:
    company_avg = await self.result_repo.get_average_score(user_id, company_id)
    system_avg = await self.result_repo.get_average_score(user_id)
    return UserQuizStatsResponse(
      user_id=user_id,
      company_average_score=company_avg,
      system_average_score=system_avg
    )
