from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.company_member import CompanyMemberResponse, CompanyAdminsResponse
from app.core.dependencies import get_current_user, get_db
from app.services.company_role import CompanyAdminService
from app.models.company_member import CompanyRole
from app.models.user import User

router = APIRouter(tags=["company-role"])

# Отримати список адміністраторів компанії
@router.get(
  "/{company_id}", 
  response_model=CompanyAdminsResponse
)
async def list_admins(
  company_id: UUID,
  current_user: User = Depends(get_current_user),
  db: AsyncSession = Depends(get_db)
):
  service = CompanyAdminService(db)
  admins = await service.get_list_admins(company_id, current_user.id)
  return CompanyAdminsResponse(admins=admins)

# Призначити користувача адміністратором
@router.post(
  "/{company_id}/admin/{user_id}", 
  response_model=CompanyMemberResponse, 
)
async def set_role_admin(
  company_id: UUID,
  user_id: UUID,
  current_user: User = Depends(get_current_user),
  db: AsyncSession = Depends(get_db)
):
  service = CompanyAdminService(db)
  return await service.change_member_role(company_id, current_user.id, user_id, role=CompanyRole.admin)

# Призначити користувача членом компанії
@router.post(
  "/{company_id}/member/{user_id}", 
  response_model=CompanyMemberResponse, 
)
async def set_role_member(
  company_id: UUID,
  user_id: UUID,
  current_user: User = Depends(get_current_user),
  db: AsyncSession = Depends(get_db)
):
  service = CompanyAdminService(db)
  return await service.change_member_role(company_id, current_user.id, user_id, role=CompanyRole.member)

# Вилучити адміністратора/члена компанії
@router.delete(
  "/{company_id}/remove/{user_id}"
)
async def remove_admin(
  company_id: UUID,
  user_id: UUID,
  current_user: User = Depends(get_current_user),
  db: AsyncSession = Depends(get_db)
):
  service = CompanyAdminService(db)
  await service.remove_admin(company_id, current_user.id, user_id)
  # return {"detail": "Admin removed successfully"}
