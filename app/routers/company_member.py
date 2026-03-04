from uuid import UUID
from fastapi import APIRouter, Depends, Query, status

from app.core.dependencies import get_current_user, get_company_member_service
from app.models.user import User
from app.schemas.company_member import CompanyMemberResponse
from app.services.company_member import CompanyMemberService

router = APIRouter(tags=["company-members"])

# Отримати всіх учасників компанії
@router.get(
  "/{company_id}/members",
  response_model=list[CompanyMemberResponse],
  status_code=status.HTTP_200_OK
)
async def get_members_of_company(
  company_id: UUID,
  limit: int = Query(50, ge=1, le=100), 
  offset: int = Query(0, ge=0),
  current_user: User = Depends(get_current_user),
  service: CompanyMemberService = Depends(get_company_member_service)
):
  return await service.get_members(company_id, limit, offset)

# Власник видаляє користувача
@router.delete(
  "/{company_id}/remove-member/{member_id}",
  status_code=status.HTTP_204_NO_CONTENT
)
async def remove_member_by_company_owner(
  company_id: UUID,
  member_id: UUID,
  current_user: User = Depends(get_current_user),
  service: CompanyMemberService = Depends(get_company_member_service)
):
  await service.remove_member(company_id, member_id, current_user)

# Користувач сам залишає компанію
@router.delete(
  "/{company_id}/member-leave/{member_id}",
  status_code=status.HTTP_204_NO_CONTENT
)
async def leave_company_by_member(
  company_id: UUID,
  member_id: UUID,
  current_user: User = Depends(get_current_user),
  service: CompanyMemberService = Depends(get_company_member_service)
):
  await service.leave_company(company_id, member_id, current_user)
