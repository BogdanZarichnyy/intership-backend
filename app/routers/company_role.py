from uuid import UUID
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.company_member import CompanyMemberResponse, CompanyAdminsResponse
from app.core.dependencies import get_current_user, get_db
from app.services.company_role import CompanyAdminService
from app.models.company_member import CompanyRole
from app.models.user import User

router = APIRouter(tags=["company-role"])

# Dependency для сервісу
async def get_admin_service(
  db: AsyncSession = Depends(get_db)
) -> CompanyAdminService:
  return CompanyAdminService(db)

# Отримати список адміністраторів компанії
@router.get(
  "/{company_id}",
  response_model=CompanyAdminsResponse,
  status_code=status.HTTP_200_OK
)
async def list_admins(
  company_id: UUID,
  current_user: User = Depends(get_current_user),
  service: CompanyAdminService = Depends(get_admin_service)
):
  admins = await service.get_list_admins(company_id, current_user.id)
  return CompanyAdminsResponse(admins)

# Призначити користувача адміністратором
@router.post(
  "/{company_id}/admin/{user_id}",
  response_model=CompanyMemberResponse,
  status_code=status.HTTP_201_CREATED
)
async def set_role_admin(
  company_id: UUID,
  user_id: UUID,
  current_user: User = Depends(get_current_user),
  service: CompanyAdminService = Depends(get_admin_service)
):
  return await service.change_member_role(company_id, current_user.id, user_id, role=CompanyRole.admin)

# Призначити користувача членом компанії
@router.post(
  "/{company_id}/member/{user_id}",
  response_model=CompanyMemberResponse,
  status_code=status.HTTP_201_CREATED
)
async def set_role_member(
  company_id: UUID,
  user_id: UUID,
  current_user: User = Depends(get_current_user),
  service: CompanyAdminService = Depends(get_admin_service)
):
  return await service.change_member_role(company_id, current_user.id, user_id, role=CompanyRole.member)

# Вилучити адміністратора/члена компанії
@router.delete(
  "/{company_id}/remove/{user_id}",
  status_code=status.HTTP_204_NO_CONTENT
)
async def remove_admin(
  company_id: UUID,
  user_id: UUID,
  current_user: User = Depends(get_current_user),
  service: CompanyAdminService = Depends(get_admin_service)
):
  await service.remove_admin(company_id, current_user.id, user_id)
  return
