from uuid import UUID
from fastapi import APIRouter, Depends, status
from app.core.dependencies import get_current_user, get_company_admin_service
from app.models.user import User
from app.models.company_member import CompanyRole
from app.schemas.company_member import CompanyMemberResponse, CompanyAdminsResponse
from app.services.company_role import CompanyAdminService

router = APIRouter(tags=["company-role"])

# Отримати список адміністраторів компанії
@router.get(
  "/{company_id}",
  response_model=CompanyAdminsResponse,
  status_code=status.HTTP_200_OK
)
async def list_admins(
  company_id: UUID,
  current_user: User = Depends(get_current_user),
  service: CompanyAdminService = Depends(get_company_admin_service)
):
  return await service.get_list_admins(company_id, current_user)

# Призначити користувача адміністратором
@router.patch(
  "/{company_id}/admin/{user_id}",
  response_model=CompanyMemberResponse,
  status_code=status.HTTP_200_OK
)
async def set_role_admin(
  company_id: UUID,
  user_id: UUID,
  current_user: User = Depends(get_current_user),
  service: CompanyAdminService = Depends(get_company_admin_service)
):
  return await service.change_member_role(company_id, user_id, current_user, role=CompanyRole.admin)

# Призначити користувача членом компанії
@router.patch(
  "/{company_id}/member/{user_id}",
  response_model=CompanyMemberResponse,
  status_code=status.HTTP_200_OK
)
async def set_role_member(
  company_id: UUID,
  user_id: UUID,
  current_user: User = Depends(get_current_user),
  service: CompanyAdminService = Depends(get_company_admin_service)
):
  return await service.change_member_role(company_id, user_id, current_user, role=CompanyRole.member)

# Вилучити адміністратора з компанії
@router.delete(
  "/{company_id}/remove/{user_id}",
  status_code=status.HTTP_204_NO_CONTENT
)
async def remove_admin(
  company_id: UUID,
  user_id: UUID,
  current_user: User = Depends(get_current_user),
  service: CompanyAdminService = Depends(get_company_admin_service)
):
  await service.remove_admin(company_id, user_id, current_user)
