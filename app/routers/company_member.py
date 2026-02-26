from fastapi import APIRouter, Depends, Query
from uuid import UUID

from app.core.dependencies import get_current_user
from app.schemas.user import UserDetailResponse
from app.schemas.company_member import CompanyMembersResponse
from app.services.company_member import CompanyMemberService
from app.db.postgres import get_db
from app.repositories.company_member import CompanyMemberRepository
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(tags=["company-members"])

# Dependency
async def get_service(db: AsyncSession = Depends(get_db)) -> CompanyMemberService:
  repo = CompanyMemberRepository(db)
  return CompanyMemberService(repo)

# Власник видаляє користувача
@router.delete(
  "/{company_id}/{member_id}", 
  response_model=None
)
async def remove_member_by_company_owner(
  company_id: UUID,
  member_id: UUID,
  current_user: UserDetailResponse = Depends(get_current_user),
  service: CompanyMemberService = Depends(get_service)
):
  await service.remove_member(
    company_id, 
    member_id,
    current_user
  )
  return {"detail": "Member removed successfully"}

# Користувач сам залишає компанію
@router.delete(
  "/leave/{company_id}", 
  response_model=None
)
async def leave_company_by_member(
  company_id: UUID,
  current_user: UserDetailResponse = Depends(get_current_user),
  service: CompanyMemberService = Depends(get_service)
):
  await service.leave_company(company_id, current_user)
  return {"detail": "You have left the company"}

# Отримати всіх учасників компанії
@router.get(
  "/{company_id}/members", 
  response_model=list[CompanyMembersResponse]
)
async def get_members_of_company(
  company_id: UUID,
  limit: int = Query(50, ge=1, le=200),   # обмеження мін/макс для безпеки
  offset: int = Query(0, ge=0),
  current_user: UserDetailResponse = Depends(get_current_user),
  service: CompanyMemberService = Depends(get_service)
):
  return await service.get_members(company_id, limit, offset)
