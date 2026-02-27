from uuid import UUID

from app.models.company import Company
from app.models.user import User

from app.schemas.company import (
  CompanySchema,
  CompanyCreateRequest,
  CompanyUpdateRequest,
  CompaniesListResponse,
  CompanyDetailResponse
)

from app.repositories.company import CompanyRepository
from app.core.exceptions import (
  CompanyNotFound,
  CompanyForbidden,
  CompanyUpdateForbidden,
  CompanyDeleteForbidden
)
from app.core.logger import logger
from app.middleware.logger_middleware import request_id_var, current_user_id_var

class CompanyService:

  def __init__(
    self,
    repository: CompanyRepository
  ):
    self.repo = repository

  async def get_all_companies(
    self,
    limit: int,
    offset: int,
  ) -> CompaniesListResponse:
    companies = await self.repo.get_all_visible_companies(
      limit,
      offset
    )
    total = await self.repo.count_visible_companies()
    logger.bind(
      request_id=request_id_var.get(), 
      user_id=current_user_id_var.get()
    ).info(f"Fetched visible companies limit={limit} offset={offset}")
    return CompaniesListResponse(
      companies=[
        CompanySchema.model_validate(c)
        for c in companies
      ],
      total=total
    )

  async def get_company_by_id(
    self,
    company_id: UUID,
    current_user: User
  ) -> Company:
    company = await self.repo.get_company_by_id(
      company_id
    )
    if not company:
      logger.bind(
        request_id=request_id_var.get(), 
        user_id=current_user_id_var.get()
      ).warning(f"Company not found id={company_id}")
      raise CompanyNotFound()
    if (
      company.owner_id != current_user.id
      and not company.is_visible
    ):
      logger.bind(
        request_id=request_id_var.get(), 
        user_id=current_user_id_var.get()
      ).warning(f"User {current_user.id} tried to access hidden company {company_id}")
      raise CompanyForbidden()
    logger.bind(
      request_id=request_id_var.get(), 
      user_id=current_user_id_var.get()
    ).info(f"Fetched company id={company_id}")
    return company

  async def create_company(
    self,
    owner: User,
    company_data: CompanyCreateRequest
  ) -> CompanyDetailResponse:
    company = Company(
      name=company_data.name,
      description=company_data.description,
      is_visible=company_data.is_visible,
      owner_id=owner.id
    )
    company = await self.repo.create_company(
      company
    )
    logger.bind(
      request_id=request_id_var.get(), 
      user_id=current_user_id_var.get()
    ).info(f"Company created id={company.id}")
    return CompanyDetailResponse.model_validate(
      company
    )

  async def update_company(
    self,
    company: Company,
    current_user: User,
    update_data: CompanyUpdateRequest
  ) -> CompanyDetailResponse:
    if company.owner_id != current_user.id:
      logger.bind(
        request_id=request_id_var.get(), 
        user_id=current_user_id_var.get()
      ).warning("Only owner can update company")
      raise CompanyUpdateForbidden()
    if update_data.name is not None:
      company.name = update_data.name
    if update_data.description is not None:
      company.description = update_data.description
    if update_data.is_visible is not None:
      company.is_visible = update_data.is_visible
    company = await self.repo.update_company(company)
    logger.bind(
      request_id=request_id_var.get(), 
      user_id=current_user_id_var.get()
    ).info(f"Company updated id={company.id}")
    return CompanyDetailResponse.model_validate(
      company
    )

  async def delete_company(
    self,
    company: Company,
    current_user: User
  ) -> None:
    if company.owner_id != current_user.id:
      logger.bind(
        request_id=request_id_var.get(), 
        user_id=current_user_id_var.get()
      ).warning("Only owner can delete company")
      raise CompanyDeleteForbidden()
    await self.repo.delete_company(company)
    logger.bind(
      request_id=request_id_var.get(), 
      user_id=current_user_id_var.get()
    ).info(f"Company deleted id={company.id}")
