import enum
import uuid
from sqlalchemy import Enum, DateTime, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.postgres import Base

class InvitationStatus(str, enum.Enum):
  pending = "pending"
  accepted = "accepted"
  declined = "declined"
  cancelled = "cancelled"

class CompanyInvitation(Base):
  __tablename__ = "company_invitations"

  id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
  company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
  invited_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
  invited_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
  status: Mapped[InvitationStatus] = mapped_column(Enum(InvitationStatus), nullable=False, default=InvitationStatus.pending)
  created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())
  updated_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

  company = relationship("Company", back_populates="invitations")
  invited_by_user = relationship("User", foreign_keys=[invited_by])
