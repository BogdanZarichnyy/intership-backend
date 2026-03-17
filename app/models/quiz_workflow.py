import uuid
from sqlalchemy import ForeignKey, DateTime, func, UniqueConstraint, Index
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from app.db.postgres import Base

class QuizWorkflow(Base):
  __tablename__ = "quiz_workflow"
  __table_args__ = (
    UniqueConstraint(
      "user_id",
      "company_id",
      "quiz_id",
      name="uq_user_company_quiz"
    ),
    Index("idx_quiz_workflow_company_time", "company_id", "updated_at"),  # Додаємо індекс для company_id - це пришвидшить пошук та обрахунок аналітичних запитів
    Index("idx_quiz_workflow_user_time", "user_id", "updated_at"),        # Додаємо індекс для user_id - це пришвидшить пошук та обрахунок аналітичних запитів
  )

  id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
  user_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
  company_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
  quiz_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False, index=True)
  correct_answers: Mapped[int] = mapped_column(default=0)
  total_questions: Mapped[int] = mapped_column(default=0)
  score: Mapped[float] = mapped_column(default=0.0)  # від 0 до 1
  created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
  updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

  user = relationship("User", back_populates="quiz_workflow")
  company = relationship("Company", back_populates="quiz_workflow")
  quiz = relationship("Quiz", back_populates="quiz_workflow")
