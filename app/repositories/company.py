from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, update, delete, func, or_
from app.models.company import Company

class CompanyRepository:

  def __init__(self, db: AsyncSession):
    self.db = db
  
  async def get_all_visible_companies(
    self,
    user_id: UUID,
    limit: int,
    offset: int
  ) -> list[Company]:
    query = (
      select(Company)
      .where(
        or_(
          Company.is_visible.is_(True),
          Company.owner_id == user_id
        )
      )
      .order_by(Company.created_at.desc())
      .limit(limit)
      .offset(offset)
    )
    result = await self.db.execute(query)
    return result.scalars().all()

  async def count_visible_companies(
    self,
    user_id: UUID
  ) -> int:
    query = (
      select(func.count())
      .select_from(Company)
      .where(
        or_(
          Company.is_visible.is_(True),
          Company.owner_id == user_id
        )
      )
    )
    result = await self.db.execute(query)
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
    data: dict
  ) -> Company:
    query = (
      insert(Company)
      .values(**data)
      .returning(Company)
    )
    result = await self.db.execute(query)
    await self.db.commit()
    return result.scalar_one()

  async def update_company(
    self,
    company_id: UUID,
    new_data: dict
  ) -> Company:    
    # for field, value in new_data.items():   # Цей код робить динамічне оновлення атрибутів об’єкта Company, потрібно передавати тоді не {company_id: UUID}, а {company: Company} як модель
    #   setattr(company, field, value)        # Це часто використовують у репозиторіях чи сервісах для оновлення моделі через словник, щоб не писати багато company.field = value вручну
    query = (
      update(Company)
      .where(Company.id == company_id)
      .values(**new_data)
      .execution_options(synchronize_session="fetch")
      .returning(Company)
    )
    result = await self.db.execute(query)
    await self.db.commit()
    return result.scalar_one()

  async def delete_company(
    self,
    company_id: UUID,
  ) -> None:
    query = delete(Company).where(Company.id == company_id)
    await self.db.execute(query)
    await self.db.commit()
