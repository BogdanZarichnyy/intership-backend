from uuid import UUID

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company_member import CompanyMember, CompanyRole

class CompanyMemberRepository:

  def __init__(self, db: AsyncSession):
    self.db = db

  async def add_member(self, company_id: UUID, user_id: UUID, role: CompanyRole = CompanyRole.member):
    member = CompanyMember(
      company_id=company_id,
      member_id=user_id,
      role=role
    )
    self.db.add(member)
    await self.db.commit()
    return member

  async def remove_member(self, company_id: UUID, user_id: UUID):
    await self.db.execute(
      delete(CompanyMember)
      .where(
        CompanyMember.company_id == company_id,
        CompanyMember.member_id == user_id
      )
    )

  async def get_all_members_for_current_company(
    self, 
    company_id: UUID, 
    role: CompanyRole | None = None,  # Метод отримання адмінів/членів компанії
    limit: int = 100, 
    offset: int = 0
  ):
    stmt = select(CompanyMember).where(
      CompanyMember.company_id == company_id,
    )
    if role:
      stmt = stmt.where(CompanyMember.role == role)
    stmt = stmt.limit(limit).offset(offset)
    result = await self.db.execute(stmt)
    return result.scalars().all()
  
  async def get_member(
    self, 
    company_id: UUID, 
    user_id: UUID, 
    role: CompanyRole = CompanyRole.admin
  ) -> CompanyMember | None:
    result = await self.db.execute(
      select(CompanyMember).where(
        CompanyMember.company_id == company_id,
        CompanyMember.member_id == user_id,
        CompanyMember.role == role
      )
    )
    return result.scalar_one_or_none()
  
  async def set_role(self, member: CompanyMember, role: CompanyRole):
    member.role = role
    await self.db.commit()
    await self.db.refresh(member)
    return member
