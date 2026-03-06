from uuid import UUID
from typing import Tuple
from app.models.company import Company
from app.models.user import User
from app.schemas.company import CompanyCreateRequest, CompanyUpdateRequest
from app.repositories.company import CompanyRepository
from app.core.exceptions import (
  CompanyNotFound,
  CompanyForbidden
)
from app.core.logger import logger

class CompanyService:

  def __init__(self, repository: CompanyRepository):
    self.repo = repository

  async def get_all_companies(
    self,
    current_user: User,
    limit: int,
    offset: int
  ) -> Tuple[list[Company], int]:
    companies = await self.repo.get_all_visible_companies(current_user.id, limit, offset)
    total = await self.repo.count_visible_companies(current_user.id,)
    logger.info(f"Fetched visible companies limit={limit} offset={offset}")
    return companies, total

  async def get_company_by_id(
    self,
    company_id: UUID,
    current_user: User,
  ) -> Company:
    company = await self.repo.get_company_by_id(company_id)
    if not company:
      logger.warning(f"Company not found id={company_id}")
      raise CompanyNotFound()
    if company.owner_id != current_user.id and not company.is_visible:
      logger.warning(f"User tried to access hidden company {company_id}")
      raise CompanyForbidden()
    logger.info(f"Fetched company id={company_id}")
    return company

  async def create_company(
    self,
    owner: User,
    company_data: CompanyCreateRequest,
  ) -> Company:
    data = company_data.model_dump()
    data["owner_id"] = owner.id
    company = await self.repo.create_company(data)
    logger.info(f"Company created id={company.id}")
    return company

  async def update_company(
    self,
    company_id: UUID,
    current_user: User,
    update_data: CompanyUpdateRequest,
  ) -> Company:
    company = await self.repo.get_company_by_id(company_id)
    if not company:
      logger.warning(f"Company not found id={company_id}")
      raise CompanyNotFound()
    if company.owner_id != current_user.id:
      logger.warning(f"Only owner can update company id={company.id}")
      raise CompanyNotFound()
    new_data = update_data.model_dump(exclude_none=True)
    if not new_data:
      logger.warning(f"Empty update payload for company id={company.id} by user id={current_user.id}")
      raise CompanyForbidden(f"Empty update payload for company id={company.id} by user id={current_user.id}")
    company = await self.repo.update_company(company, new_data)
    logger.info(f"Company updated id={company.id}")
    return company

  async def delete_company(
    self,
    company_id: UUID,
    current_user: User,
  ) -> None:
    company = await self.repo.get_company_by_id(company_id)
    if not company:
      logger.warning(f"Company not found id={company_id}")
      raise CompanyNotFound()
    if company.owner_id != current_user.id:
      logger.warning(f"Only owner can delete company id={company.id}")
      raise CompanyNotFound()
    await self.repo.delete_company(company)
    logger.info(f"Company deleted id={company.id}")
