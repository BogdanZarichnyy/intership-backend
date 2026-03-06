from uuid import UUID

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company_member import CompanyMember

class CompanyMemberRepository:

  def __init__(self, db: AsyncSession):
    self.db = db

  async def add_member(
    self, 
    company_id: UUID,
    user_id: UUID
  ):
    member = CompanyMember(
      company_id=company_id,
      member_id=user_id
    )
    self.db.add(member)
    await self.db.commit()
    return member
  
  async def get_member_of_company(
    self, 
    company_id: UUID, 
    user_id: UUID
  ) -> CompanyMember | None:
    result = await self.db.execute(
      select(CompanyMember).where(
        CompanyMember.company_id == company_id,
        CompanyMember.member_id == user_id
      )
    )
    return result.scalar_one_or_none()

  async def remove_member(
    self, 
    company_id: UUID, 
    user_id: UUID
  ):
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
    limit: int = 100, 
    offset: int = 0
  ):
    result = await self.db.execute(
      select(CompanyMember)
      .where(
        CompanyMember.company_id == company_id,
      )
      .limit(limit)
      .offset(offset)
    )
    return result.scalars().all()
