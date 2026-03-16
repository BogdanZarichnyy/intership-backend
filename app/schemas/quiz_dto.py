from app.schemas.quiz import QuizSchema, QuizQuestionResponse, QuizAnswerOptionSchema
from app.models.quiz import Quiz

def quiz_to_schema(quiz: Quiz) -> QuizSchema:
  """
  Конвертує ORM-об'єкт Quiz у Pydantic-схему QuizSchema
  """
  return QuizSchema(
    id=quiz.id,
    company_id=quiz.company_id,
    title=quiz.title,
    description=quiz.description,
    participation_count=quiz.participation_count,
    questions=[
      QuizQuestionResponse(
        id=q.id,
        title=q.title,
        allows_multiple_correct=q.allows_multiple_correct,
        options=[
          QuizAnswerOptionSchema(
            text=o.text,
            is_correct=o.is_correct
          ) for o in q.options
        ]
      )
      for q in quiz.questions
    ]
  )

def quizzes_to_list_schema(quizzes: list[Quiz], total: int) -> dict:
  """
  Конвертує список ORM-об'єктів Quiz у формат відповіді для списку
  """
  return {
    "quizzes": [quiz_to_schema(q) for q in quizzes],
    "total": total
  }