from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert, select, update, delete
from app.models.company_member import CompanyMember, CompanyRole

class CompanyMemberRepository:

  def __init__(self, db: AsyncSession):
    self.db = db

  async def add_member(
    self, 
    company_id: UUID,
    user_id: UUID
  ) -> CompanyMember:
    query = (
      insert(CompanyMember)
      .values(
        company_id=company_id,
        member_id=user_id
      )
      .returning(CompanyMember)
    )
    result = await self.db.execute(query)
    await self.db.commit()
    return result
  
  async def get_member_of_company(
    self, 
    company_id: UUID, 
    user_id: UUID
  ) -> CompanyMember | None:
    query = (
      select(CompanyMember)
      .where(
        CompanyMember.company_id == company_id,
        CompanyMember.member_id == user_id
      )
    )
    result = await self.db.execute(query)
    return result.scalar_one_or_none()

  async def remove_member(
    self, 
    company_id: UUID, 
    user_id: UUID
  ) -> None:
    await self.db.execute(
      delete(CompanyMember)
      .where(
        CompanyMember.company_id == company_id,
        CompanyMember.member_id == user_id
      )
    )
    await self.db.commit()

  async def get_all_members_for_current_company(
    self,
    company_id: UUID,
    role: CompanyRole | None = None,
    limit: int = 100, 
    offset: int = 0
  ) -> list[CompanyMember]:
    query = (
      select(CompanyMember)
      .where(CompanyMember.company_id == company_id)
    )
    if role is not None:
      query = query.where(CompanyMember.role == role)
    query = query.limit(limit).offset(offset)
    result = await self.db.execute(query)
    return result.scalars().all()

  async def set_role(
    self, 
    company_id: UUID, 
    member_id: UUID, 
    role: CompanyRole
  ) -> CompanyMember:
    query = (
      update(CompanyMember)
      .where(
          CompanyMember.company_id == company_id,
          CompanyMember.member_id == member_id
      )
      .values(role=role)
      .execution_options(synchronize_session="fetch")
      .returning(CompanyMember)
    )
    result = await self.db.execute(query)
    return result.scalar_one_or_none()

  async def get_all_members_for_notifications(
    self,
    company_id: UUID,
  ) -> list[CompanyMember]:
    query = (
      select(CompanyMember)
      .where(CompanyMember.company_id == company_id)
    )
    result = await self.db.execute(query)
    return result.scalars().all()
  
  async def get_all_members_for_notifications_for_all_companies(
    self,
  ) -> list[CompanyMember]:
    query = select(CompanyMember)
    result = await self.db.execute(query)
    return result.scalars().all()
