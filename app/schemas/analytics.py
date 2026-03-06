from uuid import UUID
from datetime import datetime
from pydantic import BaseModel
from typing import Optional

class UserOverallRatingResponse(BaseModel):
  user_id: UUID
  average_score: float

class UserQuizAverageScoreResponse(BaseModel):
  quiz_id: UUID
  title: str
  average_score: float  # заокруглений до 2 знаків
  last_attempt: datetime

class UserQuizLastAttemptResponse(BaseModel):
  id: UUID
  title: str
  updated_at: Optional[datetime] = None  # None, якщо participation_count == 0

class CompanyMemberAverageScore(BaseModel):
  user_id: UUID
  username: str
  average_score: float
  last_attempt: datetime

class QuizAverageScore(BaseModel):
  quiz_id: UUID
  title: str
  average_score: float
  last_attempt: datetime | None

class CompanyQuizAverageScore(BaseModel):
  user_id: UUID
  username: str
  average_scores_quizzes: list[QuizAverageScore]

class CompanyMemberLastAttempt(BaseModel):
  user_id: UUID
  username: str
  updated_at: datetime | None

class CompanyMemberLastAttemptsResponse(BaseModel):
  id: UUID
  name: str
  description: str
  list_company_members: list[CompanyMemberLastAttempt]
