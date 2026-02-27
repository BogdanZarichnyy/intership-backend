from uuid import UUID
from app.repositories.company_member import CompanyMemberRepository
from app.schemas.user import UserDetailResponse
from app.schemas.company_member import CompanyMemberCreate
from app.core.exceptions import CompanyOwnerOnly, CompanyMembershipForbidden

from app.core.logger import logger
from app.middleware.logger_middleware import request_id_var, current_user_id_var

class CompanyMemberService:

  def __init__(self, repository: CompanyMemberRepository):
    self.repository = repository

  async def add_member(
    self, 
    data: CompanyMemberCreate,
    current_user: UserDetailResponse
  ):
    # Перевірка, чи current_user є власником компанії
    if not current_user.is_owner_of_company(data.company_id):
      logger.bind(
        request_id=request_id_var.get(), 
        user_id=current_user_id_var.get()
      ).warning(f"User is not owner of company id={data.company_id}")
      raise CompanyOwnerOnly("Only owners can add members")
    return await self.repository.add_member(
      company_id=data.company_id,
      user_id=data.member_id
    )

  async def remove_member(
    self, 
    company_id: UUID, 
    member_id: UUID, 
    current_user: UserDetailResponse
  ):
    # Перевірка, чи current_user є власником компанії
    if not current_user.is_owner_of_company(company_id):
      logger.bind(
        request_id=request_id_var.get(), 
        user_id=current_user_id_var.get()
      ).warning(f"User is not owner of company {company_id}")
      raise CompanyOwnerOnly("Only owners can remove members")
    await self.repository.remove_member(company_id, member_id)
    logger.bind(
      request_id=request_id_var.get(), 
      user_id=current_user_id_var.get()
    ).info(f"Owner removed from company id={company_id} member {member_id}")

  async def leave_company(
    self, 
    company_id: UUID, 
    current_user: UserDetailResponse
  ):
    # Перевірка, що користувач видаляє тільки себе
    if not current_user.is_member_of_company(company_id):
      logger.bind(
        request_id=request_id_var.get(), 
        user_id=current_user_id_var.get()
      ).warning(f"User is not member of company {company_id}")
      raise CompanyMembershipForbidden("You can only leave your own company membership")
    await self.repository.remove_member(company_id, current_user.id)
    logger.bind(
      request_id=request_id_var.get(), 
      user_id=current_user_id_var.get()
    ).info(f"Member leave company {company_id}")

  async def get_members(
    self, 
    company_id: UUID, 
    limit: int = 100, 
    offset: int = 0
  ):
    # Отримати всіх учасників компанії
    logger.bind(
      request_id=request_id_var.get(), 
      user_id=current_user_id_var.get()
    ).info(f"Fetched members of company list company {company_id} limit={limit} offset={offset}")
    return await self.repository.get_all_members_for_current_company(
      company_id=company_id,
      limit=limit,
      offset=offset
    )
