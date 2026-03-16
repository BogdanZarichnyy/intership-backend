from uuid import UUID
from app.core.logger import logger
from app.core.exceptions import QuizForbidden
from app.models.quiz import Quiz, QuizQuestion, QuizAnswerOption
from app.schemas.quiz_workflow import QuizAttemptRequest

class QuizWorkflowCalculator:
  def __init__(
    self,
    correct_answers: int,
    total_questions: int,
    score: float,
    answers_for_cache: list[dict]
  ):
    self.correct_answers = correct_answers
    self.total_questions = total_questions
    self.score = score
    self.answers_for_cache = answers_for_cache

def calculate_quiz_result(
  quiz: Quiz,
  payload: QuizAttemptRequest,
  user_id: UUID
) -> QuizWorkflowCalculator:
  """
  Підрахунок правильних відповідей та оцінки для квіза.
  Всі перевірки на дублі, чужі питання та варіанти відбуваються тут.
  """
  questions: list[QuizQuestion] = quiz.questions
  # мапа питань
  question_map: dict[UUID, QuizQuestion] = {question.id: question for question in questions}
  # 1. Валідація вхідних даних (payload)
  submitted_question_ids = [answer.question_id for answer in payload.answers]
  submitted_question_set = set(submitted_question_ids)
  quiz_question_set = set(question_map.keys())
  logger.debug(f"User {user_id} submitted {len(submitted_question_ids)} answers")
  # 2. Duplicate question IDs
  if len(submitted_question_ids) != len(submitted_question_set):
    logger.warning(f"Duplicate question IDs detected (user={user_id}, quiz={quiz.id})")
    raise QuizForbidden("Duplicate question IDs in submission")
  # 3. Foreign question IDs
  extra_questions = submitted_question_set - quiz_question_set
  if extra_questions:
    logger.warning(f"Invalid question IDs {extra_questions} (user={user_id}, quiz={quiz.id})")
    raise QuizForbidden("Submission contains questions not belonging to this quiz")
  # 4. Missing questions
  if submitted_question_set != quiz_question_set:
    missing = quiz_question_set - submitted_question_set
    logger.warning(f"Incomplete submission. Missing: {missing} (user={user_id}, quiz={quiz.id})")
    raise QuizForbidden("All quiz questions must be answered")
  logger.debug(f"Question-level validation passed (user={user_id}, quiz={quiz.id})")
  # 5. Підрахунок результатів
  correct_answers = 0
  answers_for_cache = []  # формуємо структуру відповідей для Redis
  for answer in payload.answers:
    question = question_map[answer.question_id]
    options: list[QuizAnswerOption] = question.options
    # мапа валідних опцій
    option_map = {option.id: option for option in options}
    selected_set = set(answer.selected_option_ids)
    # single choise validation
    if not question.allows_multiple_correct and len(selected_set) > 1:
      logger.warning(f"Multiple answers submitted for single-choice question {question.id} (user={user_id})")
      raise QuizForbidden("This question allows only one answer")
    # Duplicate option IDs
    if len(selected_set) != len(answer.selected_option_ids):
      logger.warning(f"Duplicate option IDs in question {question.id} (user={user_id})")
      raise QuizForbidden("Duplicate answer options detected")
    # Foreign option IDs
    invalid_options = selected_set - set(option_map.keys())
    if invalid_options:
      logger.warning(f"Invalid option IDs {invalid_options} for question {question.id} (user={user_id})")
      raise QuizForbidden("Answer contains options not belonging to this question")
    # мапа правильних відповідей
    correct_set = {option.id for option in options if option.is_correct}  # формуємо мапу відповідей для Redis
    selected_options = []
    for option_id in selected_set:
      option_obj = option_map[option_id]
      selected_options.append({
        "answer": str(option_id),
        "is_correct": option_obj.is_correct
      })
    answers_for_cache.append({
      "question_id": str(answer.question_id),
      "selected_options": selected_options
    })
    if selected_set == correct_set:
      correct_answers += 1
      logger.debug(f"Question {question.id} answered correctly by user {user_id}")
    else:
      logger.debug(f"Question {question.id} answered incorrectly by user {user_id}")
  total_questions = len(questions)
  score = correct_answers / total_questions if total_questions else 0.0
  logger.info(f"User {user_id} scored {score:.2f} on quiz {quiz.id}")
  return QuizWorkflowCalculator(correct_answers, total_questions, score, answers_for_cache)
