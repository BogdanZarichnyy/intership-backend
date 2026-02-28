from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.postgres import get_db
from app.services.company import CompanyService
from app.schemas.company import (
  CompanyCreateRequest,
  CompanyUpdateRequest,
  CompaniesListResponse,
  CompanyDetailResponse
)
from app.schemas.user import UserDetailResponse
from app.core.dependencies import get_current_user
from app.repositories.company import CompanyRepository

__all__ = ["CompanyService"]

router = APIRouter(tags=["companies"])

def get_company_service(
  db: AsyncSession = Depends(get_db)
) -> CompanyService:
  return CompanyService(CompanyRepository(db))

# Отримати список компаній
@router.get(
  "/",
  response_model=CompaniesListResponse,
  summary="Get list of companies with pagination"
)
async def get_all_companies(
  limit: int = Query(
    default=10,
    ge=1,
    le=100,
    description="Number of companies per page"
  ),
  offset: int = Query(
    default=0,
    ge=0,
    description="Pagination offset"
  ),
  current_user: UserDetailResponse = Depends(get_current_user),
  service: CompanyService = Depends(get_company_service)
):
  return await service.get_all_companies(
    limit=limit,
    offset=offset,
  )

# Отримати компанію по ID
@router.get(
  "/{company_id}",
  response_model=CompanyDetailResponse,
)
async def get_company_by_id(
  company_id: UUID,
  current_user: UserDetailResponse = Depends(get_current_user),
  service: CompanyService = Depends(get_company_service)
):
  # Передаємо current_user у сервіс, щоб він міг визначити, чи є користувач власником компанії і чи можна показувати її дані
  company = await service.get_company_by_id(company_id, current_user)
  return company

# Створити компанію
@router.post(
  "/",
  response_model=CompanyDetailResponse,
)
async def create_company(
  company_data: CompanyCreateRequest,
  current_user: UserDetailResponse = Depends(get_current_user),
  service: CompanyService = Depends(get_company_service)
):
  return await service.create_company(
    owner=current_user,
    company_data=company_data
  )

# Оновити компанію (тільки owner)
@router.put(
  "/{company_id}",
  response_model=CompanyDetailResponse
)
async def update_company(
  company_id: UUID,
  update_data: CompanyUpdateRequest,
  current_user: UserDetailResponse = Depends(get_current_user),
  service: CompanyService = Depends(get_company_service)
):
  company = await service.get_company_by_id(company_id, current_user)
  return await service.update_company(
    company=company,
    current_user=current_user,
    update_data=update_data
)

# Видалити компанію (тільки owner)
@router.delete(
  "/{company_id}",
)
async def delete_company(
  company_id: UUID,
  current_user: UserDetailResponse = Depends(get_current_user),
  service: CompanyService = Depends(get_company_service)
):
  company = await service.get_company_by_id(company_id, current_user)
  await service.delete_company(
    company=company,
    current_user=current_user
  )
  return
