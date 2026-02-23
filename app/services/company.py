from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi import HTTPException, status
from app.models.company import Company
from app.models.user import User
from app.schemas.company import (
    CompanySchema,
    CompanyCreateRequest,
    CompanyUpdateRequest,
    CompaniesListResponse,
    CompanyDetailResponse
)
import logging

logger = logging.getLogger("app")

class CompanyService:
  def __init__(self, db: AsyncSession):
    self.db = db

  # Отримати список компаній (можна фільтрувати по visibility)
  async def get_all_companies(
    self,
    limit: int = 10,
    offset: int = 0,
  ) -> CompaniesListResponse:
    try:
      # Запит тільки видимих компаній
      result = await self.db.execute(
        select(Company)
        .where(Company.is_visible.is_(True))
        .order_by(Company.created_at.desc())
        .limit(limit)
        .offset(offset)
      )
      companies = result.scalars().all()
      total = len(companies)  # рахуємо кількість на основі результатів запиту
      logger.info(f"Fetched visible companies limit={limit} offset={offset}")
      return CompaniesListResponse(
        companies=[CompanySchema.model_validate(c) for c in companies],
        total=total
      )
    except Exception as e:
      await self.db.rollback()
      logger.error(f"Failed to fetch companies list: {e}")
      raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Failed to fetch companies"
      )

  # Отримати компанію по ID
  async def get_company_by_id(
    self,
    company_id: UUID,
    current_user: User
  ) -> Company | None:
    """
    Повертає компанію за ID.
    - Власник компанії отримує всі дані незалежно від is_visible.
    - Інші користувачі бачать компанію тільки якщо is_visible=True.
    """
    try:
      # Отримуємо компанію по id
      result = await self.db.execute(
        select(Company).where(Company.id == company_id)
      )
      company = result.scalar_one_or_none()
      if not company:
        logger.warning(f"Company not found id={company_id}")
        return None
      # Якщо компанія прихована
      if company.owner_id != current_user.id and not company.is_visible:
        logger.warning(f"User {current_user.id} tried to access hidden company {company_id}")
        return None
      logger.info(f"Fetched company id={company_id} for user {current_user.id}")
      return company
    except Exception as e:
      await self.db.rollback()
      logger.error(f"Failed to fetch company id={company_id}: {e}")
      raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Failed to fetch company"
      )

  # Створення компанії (owner = current_user)
  async def create_company(
      self,
      owner: User,
      company_data: CompanyCreateRequest
  ) -> CompanyDetailResponse:
    try:
      company = Company(
        name=company_data.name,
        description=company_data.description,
        is_visible=company_data.is_visible,
        owner_id=owner.id
      )
      self.db.add(company)
      await self.db.commit()
      await self.db.refresh(company)
      logger.info(
        f"Company created id={company.id} owner={owner.id}"
      )
      return CompanyDetailResponse.model_validate(company)
    except Exception as e:
      await self.db.rollback()
      logger.error(f"Failed to create company: {e}")
      raise

  # Оновлення компанії (тільки Owner)
  async def update_company(
    self,
    company: Company,
    current_user: User,
    update_data: CompanyUpdateRequest
  ) -> CompanyDetailResponse:
    try:
      if company.owner_id != current_user.id:
        raise HTTPException(
          status_code=status.HTTP_403_FORBIDDEN,
          detail="Only owner can update company"
        )
      if update_data.name is not None:
        company.name = update_data.name
      if update_data.description is not None:
        company.description = update_data.description
      if update_data.is_visible is not None:
        company.is_visible = update_data.is_visible
      await self.db.commit()
      await self.db.refresh(company)
      logger.info(
        f"Company updated id={company.id}"
      )
      return CompanyDetailResponse.model_validate(company)
    except Exception as e:
      await self.db.rollback()
      logger.error(
        f"Failed to update company id={company.id}: {e}"
      )
      raise

  # Видалення компанії (тільки Owner)
  async def delete_company(
    self,
    company: Company,
    current_user: User
  ) -> None:
    company_id = company.id  # зберігаємо id для логування після видалення
    try:
      if company.owner_id != current_user.id:
        raise HTTPException(
          status_code=status.HTTP_403_FORBIDDEN,
          detail="Only owner can delete company"
      )
      await self.db.delete(company)
      await self.db.commit()
      logger.info(
        f"Company deleted id={company_id}"
      )
    except Exception as e:
      await self.db.rollback()
      logger.error(
        f"Failed to delete company id={company_id}: {e}"
      )
      raise
