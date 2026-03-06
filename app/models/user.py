import uuid
from sqlalchemy import String, Boolean, DateTime, func, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.postgres import Base

class User(Base):
  __tablename__ = "users"
  __table_args__ = (
    UniqueConstraint("provider", "provider_id", name="uq_provider_provider_id"),
  )

  id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
  email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
  username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
  hashed_password: Mapped[str | None] = mapped_column(String(255), nullable=True)
  provider: Mapped[str] = mapped_column(String(50), nullable=False, default="local", index=True)
  provider_id: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True, index=True)
  is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
  created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())
  updated_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

  companies = relationship("Company", back_populates="owner", cascade="all, delete-orphan")
  member_companies = relationship("CompanyMember", back_populates="member", cascade="all, delete-orphan")
  invitations_sent = relationship("CompanyInvitation", back_populates="invited_by_user", foreign_keys="CompanyInvitation.invited_by")
