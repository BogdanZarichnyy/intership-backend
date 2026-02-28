from sqlalchemy import ForeignKey, DateTime, func
from sqlalchemy.orm import relationship, Mapped, mapped_column
from uuid import UUID, uuid4

from app.db.postgres import Base

class QuizResult(Base):
  __tablename__ = "quiz_results"

  id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
  user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
  company_id: Mapped[UUID] = mapped_column(ForeignKey("companies.id"))
  quiz_id: Mapped[UUID] = mapped_column(ForeignKey("quizzes.id"))
  correct_answers: Mapped[int] = mapped_column(default=0)
  total_questions: Mapped[int] = mapped_column(default=0)
  score: Mapped[float] = mapped_column(default=0.0)  # від 0 до 1
  created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())
  updated_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

  user = relationship("User", back_populates="quiz_results")
  company = relationship("Company", back_populates="quiz_results")
  quiz = relationship("Quiz", back_populates="results")
