from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, field_validator
from typing import Optional

class UserOverallRatingResponse(BaseModel):
  user_id: UUID
  username: str
  overall_rating: float

  @field_validator("overall_rating")
  def round_score(cls, value):
    return round(float(value), 2)

class UserQuizAverageScoreResponse(BaseModel):
  quiz_id: UUID
  title: str
  average_score: float  # заокруглений до 2 знаків
  last_attempt: datetime

  @field_validator("average_score")
  def round_score(cls, value):
    return round(float(value), 2)

class UserQuizLastAttemptResponse(BaseModel):
  quiz_id: UUID
  title: str
  last_attempt: datetime | None  # None, якщо participation_count == 0

class CompanyMemberAverageScore(BaseModel):
  user_id: UUID
  username: str
  average_score: float
  last_attempt: datetime

  @field_validator("average_score")
  def round_score(cls, value):
    return round(float(value), 2)

  model_config = {"populate_by_name": True}  # щоб alias працював

class QuizAverageScore(BaseModel):
  quiz_id: UUID
  title: str
  average_score: float
  last_attempt: datetime | None

  @field_validator("average_score")
  def round_score(cls, value):
    return round(float(value), 2)

class CompanyQuizAverageScore(BaseModel):
  user_id: UUID
  username: str
  average_scores_quizzes: list[QuizAverageScore]

class CompanyMemberLastAttempt(BaseModel):
  user_id: UUID
  username: str
  last_attempt: datetime | None

class CompanyMemberLastAttemptsResponse(BaseModel):
  company_id: UUID
  name: str
  description: str
  list_company_members: list[CompanyMemberLastAttempt]
