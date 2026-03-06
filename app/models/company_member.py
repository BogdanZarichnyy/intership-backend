import uuid
from sqlalchemy import ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.postgres import Base

class CompanyMember(Base):
  __tablename__ = "company_members"

  company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), primary_key=True)
  member_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
  created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())

  company = relationship("Company", back_populates="members")
  member = relationship("User", back_populates="member_companies")
