from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict

# Варіанти відповіді
class QuizAnswerOptionSchema(BaseModel):
  text: str
  is_correct: bool

# Питання тесту
class QuizQuestionSchema(BaseModel):
  title: str
  allows_multiple_correct: bool = False
  options: list[QuizAnswerOptionSchema]

# Запит на створення тесту
class QuizCreateRequest(BaseModel):
  title: str = Field(..., min_length=1)
  description: str | None = None
  questions: list[QuizQuestionSchema]

# Запит на оновлення тесту
class QuizUpdateRequest(BaseModel):
  title: str | None = None
  description: str | None = None
  questions: list[QuizQuestionSchema] | None = None

# Відповідь по питанню з id
class QuizQuestionResponse(BaseModel):
  id: UUID
  title: str
  allows_multiple_correct: bool
  options: list[QuizAnswerOptionSchema]

  model_config = ConfigDict(from_attributes=True)

# Повна схема тесту для відповіді API
class QuizSchema(BaseModel):
  id: UUID
  company_id: UUID
  title: str
  description: str | None
  participation_count: int  # частота проходжень
  questions: list[QuizQuestionResponse]

  model_config = ConfigDict(from_attributes=True)

# Відповідь зі списком тестів
class QuizListResponse(BaseModel):
  quizzes: list[QuizSchema]
  total: int
