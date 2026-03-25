from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime

class QuizAttemptAnswerSchema(BaseModel):
  question_id: UUID
  selected_option_ids: list[UUID] = Field(..., min_length=1)

class QuizAttemptRequest(BaseModel):
  answers: list[QuizAttemptAnswerSchema]

class QuizAttemptResponse(BaseModel):
  quiz_id: UUID
  company_id: UUID
  user_id: UUID
  correct_answers: int
  total_questions: int
  score: float
  attempted_at: datetime

  model_config = ConfigDict(from_attributes=True)

class UserQuizStatsResponse(BaseModel):
  user_id: UUID
  company_average_score: float
  system_average_score: float