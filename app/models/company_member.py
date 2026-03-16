import uuid
import enum
from sqlalchemy import Enum, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from app.db.postgres import Base

class CompanyRole(str, enum.Enum):
  member = "member"
  admin = "admin"

class CompanyMember(Base):
  __tablename__ = "company_members"

  company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), primary_key=True)
  member_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
  role: Mapped[CompanyRole] = mapped_column(Enum(CompanyRole), nullable=False, default=CompanyRole.member)
  created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
  updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

  company = relationship("Company", back_populates="members")
  member = relationship("User", back_populates="member_companies")
