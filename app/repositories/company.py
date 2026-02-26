from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.company import Company

class CompanyRepository:

  def __init__(self, db: AsyncSession):
    self.db = db

  async def get_all_visible_companies(
    self,
    limit: int,
    offset: int
  ) -> list[Company]:
    result = await self.db.execute(
      select(Company)
      .where(Company.is_visible.is_(True))
      .order_by(Company.created_at.desc())
      .limit(limit)
      .offset(offset)
    )
    return result.scalars().all()

  async def count_visible_companies(self) -> int:
    result = await self.db.execute(
      select(func.count())
      .select_from(Company)
      .where(Company.is_visible.is_(True))
    )
    return result.scalar_one()

  async def get_company_by_id(
    self,
    company_id: UUID
  ) -> Company | None:
    result = await self.db.execute(
      select(Company)
      .where(Company.id == company_id)
    )
    return result.scalar_one_or_none()

  async def create_company(
    self,
    company: Company
  ) -> Company:
    self.db.add(company)
    await self.db.commit()
    await self.db.refresh(company)
    return company

  async def update_company(
    self,
    company: Company
  ) -> Company:
    await self.db.commit()
    await self.db.refresh(company)
    return company

  async def delete_company(
    self,
    company: Company
  ) -> None:
    await self.db.delete(company)
    await self.db.commit()