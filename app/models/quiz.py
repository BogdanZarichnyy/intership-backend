import uuid
from sqlalchemy import String, Text, DateTime, Boolean, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.postgres import Base

class Quiz(Base):
  __tablename__ = "quizzes"

  id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
  company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
  title: Mapped[str] = mapped_column(String(255), nullable=False)
  description: Mapped[str | None] = mapped_column(Text, nullable=True)
  participation_count: Mapped[int] = mapped_column(default=0)  # частота участі всіх користувачів
  created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())
  updated_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

  questions = relationship("QuizQuestion", back_populates="quiz", cascade="all, delete-orphan")
  company = relationship("Company", back_populates="quizzes")

class QuizQuestion(Base):
  __tablename__ = "quiz_questions"

  id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
  quiz_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False)
  title: Mapped[str] = mapped_column(String(255), nullable=False)
  allows_multiple_correct: Mapped[bool] = mapped_column(Boolean, default=False)
  created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())
  updated_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

  quiz = relationship("Quiz", back_populates="questions")
  options = relationship("QuizAnswerOption", back_populates="question", cascade="all, delete-orphan")

class QuizAnswerOption(Base):
  __tablename__ = "quiz_answer_options"

  id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
  question_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("quiz_questions.id", ondelete="CASCADE"), nullable=False)
  text: Mapped[str] = mapped_column(String(255), nullable=False)
  is_correct: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

  question = relationship("QuizQuestion", back_populates="options")
