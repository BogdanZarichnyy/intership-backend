from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
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
  status_code=status.HTTP_200_OK
)
async def get_all_companies(
  limit: int = Query(default=10, ge=1, le=100),
  offset: int = Query(default=0, ge=0),
  current_user: UserDetailResponse = Depends(get_current_user),
  service: CompanyService = Depends(get_company_service)
):
  return await service.get_all_companies(limit, offset)

# Отримати компанію по ID
@router.get(
  "/{company_id}",
  response_model=CompanyDetailResponse,
  status_code=status.HTTP_200_OK
)
async def get_company_by_id(
  company_id: UUID,
  current_user: UserDetailResponse = Depends(get_current_user),
  service: CompanyService = Depends(get_company_service)
):
  return await service.get_company_by_id(company_id, current_user)

# Створити компанію
@router.post(
  "/",
  response_model=CompanyDetailResponse,
  status_code=status.HTTP_201_CREATED
)
async def create_company(
  company_data: CompanyCreateRequest,
  current_user: UserDetailResponse = Depends(get_current_user),
  service: CompanyService = Depends(get_company_service)
):
  return await service.create_company(current_user, company_data)

# Оновити дані про компанію може тільки власник
@router.patch(
  "/{company_id}",
  response_model=CompanyDetailResponse,
  status_code=status.HTTP_200_OK
)
async def update_company(
  company_id: UUID,
  update_data: CompanyUpdateRequest,
  current_user: UserDetailResponse = Depends(get_current_user),
  service: CompanyService = Depends(get_company_service)
):
  return await service.update_company(company_id, current_user, update_data)

# Видалити компанію може тільки власник
@router.delete(
  "/{company_id}",
  status_code=status.HTTP_204_NO_CONTENT
)
async def delete_company(
  company_id: UUID,
  current_user: UserDetailResponse = Depends(get_current_user),
  service: CompanyService = Depends(get_company_service)
):
  await service.delete_company(company_id, current_user)
  return
