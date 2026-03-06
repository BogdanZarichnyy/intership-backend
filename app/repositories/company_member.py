from uuid import UUID

from sqlalchemy import insert, select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.models.company_member import CompanyMember, CompanyRole

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
  
    # query = (
    #   insert(CompanyMember)
    #   .values(
    #     company_id=company_id,
    #     user_id=user_id
    #   )
    #   .execution_options(synchronize_session="fetch")
    #   .returning(CompanyMember)
    # )
    # result = await self.db.execute(query)
    # await self.db.commit()
    # return result
  
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
    query = (
      select(CompanyMember)
      .where(
        CompanyMember.company_id == company_id,
        CompanyMember.role == CompanyRole.admin
      )
      .limit(limit).offset(offset)
    )
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
