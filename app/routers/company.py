from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from app.services.company import CompanyService
from app.schemas.company import (
  CompanySchema,
  CompanyCreateRequest,
  CompanyUpdateRequest,
  CompaniesListResponse
)
from app.models.user import User
from app.core.dependencies import get_current_user, get_company_service

router = APIRouter(tags=["companies"])

# Отримати список компаній
@router.get(
  "/",
  response_model=CompaniesListResponse,
  status_code=status.HTTP_200_OK
)
async def get_all_companies(
  limit: int = Query(default=10, ge=1, le=100),
  offset: int = Query(default=0, ge=0),
  current_user: User = Depends(get_current_user),
  service: CompanyService = Depends(get_company_service)
):
  companies, total = await service.get_all_companies(limit, offset)
  return CompaniesListResponse(companies=companies, total=total)

# Отримати компанію по ID
@router.get(
  "/{company_id}",
  response_model=CompanySchema,
  status_code=status.HTTP_200_OK
)
async def get_company_by_id(
  company_id: UUID,
  current_user: User = Depends(get_current_user),
  service: CompanyService = Depends(get_company_service)
):
  return await service.get_company_by_id(company_id, current_user)

# Створити компанію
@router.post(
  "/",
  response_model=CompanySchema,
  status_code=status.HTTP_201_CREATED
)
async def create_company(
  company_data: CompanyCreateRequest,
  current_user: User = Depends(get_current_user),
  service: CompanyService = Depends(get_company_service)
):
  return await service.create_company(current_user, company_data)

# Оновити дані про компанію може тільки власник
@router.patch(
  "/{company_id}",
  response_model=CompanySchema,
  status_code=status.HTTP_200_OK
)
async def update_company(
  company_id: UUID,
  update_data: CompanyUpdateRequest,
  current_user: User = Depends(get_current_user),
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
  current_user: User = Depends(get_current_user),
  service: CompanyService = Depends(get_company_service)
):
  await service.delete_company(company_id, current_user)
