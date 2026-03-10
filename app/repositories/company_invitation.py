from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert, select, update, delete
from app.models.company_invitation import CompanyInvitation, InvitationStatus
from app.models.company import Company

class CompanyInvitationRepository:
  def __init__(self, db: AsyncSession):
    self.db = db

  async def create_invitation(
    self,
    data: dict
  ) -> CompanyInvitation:
    query = (
      insert(CompanyInvitation)
      .values(**data)
      .returning(CompanyInvitation)
    )
    result = await self.db.execute(query)
    await self.db.commit()
    return result.scalar_one()

  async def get_invitation_by_id(
    self,
    invitation_id: UUID
  ) -> CompanyInvitation | None:
    query = (
      select(CompanyInvitation)
      .where(CompanyInvitation.id == invitation_id)
    )
    result = await self.db.execute(query)
    return result.scalar_one_or_none()

  async def get_user_invitations(
    self,
    user_id: UUID,
    limit: int,
    offset: int
  ) -> list[CompanyInvitation]:
      query = (
        select(CompanyInvitation)
        .where(
          CompanyInvitation.invited_user_id == user_id,
          CompanyInvitation.status == InvitationStatus.pending
        )
        .order_by(CompanyInvitation.created_at.desc())
        .limit(limit)
        .offset(offset)
      )
      result = await self.db.execute(query)
      return result.scalars().all()
  
  # 1. USER → список своїх membership requests
  async def get_user_requests(
    self,
    user_id: UUID,
    limit: int,
    offset: int
  ) -> list[CompanyInvitation]:
    query = (
      select(CompanyInvitation)
      .join(
        Company,
        Company.id == CompanyInvitation.company_id
      )
      .where(
        CompanyInvitation.invited_by == user_id,
        CompanyInvitation.invited_user_id == user_id,
        CompanyInvitation.invited_by != Company.owner_id
      )
      .order_by(CompanyInvitation.created_at.desc())
      .limit(limit)
      .offset(offset)
    )
    result = await self.db.execute(query)
    return result.scalars().all()

  # 2. USER → список received invitations
  async def get_user_received_invitations(
    self,
    user_id: UUID,
    limit: int,
    offset: int
  ) -> list[CompanyInvitation]:
    query = (
      select(CompanyInvitation)
      .join(
        Company,
        Company.id == CompanyInvitation.company_id
      )
      .where(
        CompanyInvitation.invited_user_id == user_id,
        CompanyInvitation.invited_by == Company.owner_id
      )
      .order_by(CompanyInvitation.created_at.desc())
      .limit(limit)
      .offset(offset)
    )
    result = await self.db.execute(query)
    return result.scalars().all()

  # 3. OWNER → invited users
  async def get_company_invited_users(
    self,
    company_id: UUID,
    owner_id: UUID,
    limit: int,
    offset: int
  ) -> list[CompanyInvitation]:
    query = (
      select(CompanyInvitation)
      .where(
        CompanyInvitation.company_id == company_id,
        CompanyInvitation.invited_by == owner_id
      )
      .order_by(CompanyInvitation.created_at.desc())
      .limit(limit)
      .offset(offset)
    )
    result = await self.db.execute(query)
    return result.scalars().all()

  # 4. OWNER → pending membership requests
  async def get_company_membership_requests(
      self,
      company_id: UUID,
      owner_id: UUID,
      limit: int,
      offset: int
  ) -> list[CompanyInvitation]:
    query = (
      select(CompanyInvitation)
      .where(
        CompanyInvitation.company_id == company_id,
        CompanyInvitation.status == InvitationStatus.pending,
        CompanyInvitation.invited_by != owner_id
      )
      .order_by(CompanyInvitation.created_at.desc())
      .limit(limit)
      .offset(offset)
    )
    result = await self.db.execute(query)
    return result.scalars().all()

  async def update_status(
    self,
    invitation_id: UUID,
    status: InvitationStatus,
  ) -> CompanyInvitation:
    query = (
      update(CompanyInvitation)
      .where(CompanyInvitation.id == invitation_id)
      .values(status=status)
      .returning(CompanyInvitation)
    )
    result = await self.db.execute(query)
    await self.db.commit()
    return result.scalar_one_or_none()

  # delete_invitation наразі не використовується, але може знадобитися для повного видалення запрошення замість простої зміни статусу
  async def delete_invitation(
    self,
    invitation_id: UUID
  ) -> None:
    query = delete(CompanyInvitation).where(CompanyInvitation.id == invitation_id)
    await self.db.execute(query)
    await self.db.commit()
