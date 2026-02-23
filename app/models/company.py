import uuid
from sqlalchemy import String, Text, DateTime, func, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.db.postgres import Base

class Company(Base):
  __tablename__ = "companies"

  id: Mapped[uuid.UUID] = mapped_column(
    UUID(as_uuid=True),
    primary_key=True,
    default=uuid.uuid4,
    index=True
  )

  owner_id: Mapped[uuid.UUID] = mapped_column(
    UUID(as_uuid=True),
    ForeignKey("users.id", ondelete="CASCADE"),
    nullable=False,
    index=True
  )

  name: Mapped[str] = mapped_column(
    String(255),
    nullable=False,
    index=True
  )

  description: Mapped[str | None] = mapped_column(
    Text,
    nullable=True
  )

  is_visible: Mapped[bool] = mapped_column(
    Boolean,
    default=True, # True = visible to all | False = hidden
    nullable=False,
    index=True
  )

  created_at: Mapped[DateTime] = mapped_column(
    DateTime,
    server_default=func.now()
  )

  updated_at: Mapped[DateTime] = mapped_column(
    DateTime,
    server_default=func.now(),
    onupdate=func.now()
  )

  owner = relationship(
    "User",
    back_populates="companies"
  )
