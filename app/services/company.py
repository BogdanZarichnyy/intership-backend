from uuid import UUID
from app.core.logger import logger
from app.core.exceptions import (
  CompanyNotFound,
  CompanyForbidden
)
from app.models.user import User
from app.models.company import Company
from app.repositories.company import CompanyRepository
from app.schemas.company import CompanySchema, CompanyCreateRequest, CompanyUpdateRequest, CompaniesListResponse

class CompanyService:

  def __init__(self, repository: CompanyRepository):
    self.repo = repository

  async def get_all_companies(
    self,
    current_user: User,
    limit: int,
    offset: int
  ) -> CompaniesListResponse:
    companies = await self.repo.get_all_visible_companies(current_user.id, limit, offset)
    total = await self.repo.count_visible_companies(current_user.id)
    logger.info(f"Fetched visible companies limit={limit} offset={offset}")
    # Перетворюємо кожну компанію на Pydantic-модель
    companies_data = [CompanySchema.model_validate(company) for company in companies]
    # Передаємо як словник при створенні відповіді
    return CompaniesListResponse.model_validate({
      "companies": companies_data,
      "total": total
    })

  async def get_company_by_id(
    self,
    company_id: UUID,
    current_user: User,
  ) -> CompanySchema:
    company = await self.repo.get_company_by_id(company_id)
    if not company:
      logger.warning(f"Company not found id={company_id}")
      raise CompanyNotFound()
    if company.owner_id != current_user.id and not company.is_visible:
      logger.warning(f"User tried to access hidden company {company_id}")
      raise CompanyForbidden()
    logger.info(f"Fetched company id={company_id}")
    return CompanySchema.model_validate(company)

  async def create_company(
    self,
    owner: User,
    company_data: CompanyCreateRequest,
  ) -> Company:
    data = company_data.model_dump()
    data["owner_id"] = owner.id
    company = await self.repo.create_company(data)
    logger.info(f"Company created id={company.id}")
    return CompanySchema.model_validate(company)

  async def update_company(
    self,
    company_id: UUID,
    current_user: User,
    update_data: CompanyUpdateRequest,
  ) -> CompanySchema:
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
    company = await self.repo.update_company(company_id, new_data)
    logger.info(f"Company updated id={company.id}")
    return CompanySchema.model_validate(company)

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
    await self.repo.delete_company(company_id)
    logger.info(f"Company deleted id={company.id}")
