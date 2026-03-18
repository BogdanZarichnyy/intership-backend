import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Boolean, ForeignKey, func, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.postgres import Base

class Notification(Base):
  __tablename__ = "notifications"
  __table_args__ = (
    UniqueConstraint("user_id", "quiz_id", name="uq_notification_user_quiz"),
    Index("ix_notifications_user_created_at", "user_id", "created_at"),
  )

  id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
  user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
  quiz_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False, index=True)
  message: Mapped[str] = mapped_column(String(255), nullable=False)
  is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
  created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
  updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

  user = relationship("User", back_populates="notifications")
  quiz = relationship("Quiz", back_populates="notifications")
