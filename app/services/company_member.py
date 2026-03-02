from uuid import UUID
from app.repositories.company_member import CompanyMemberRepository
from app.schemas.user import UserDetailResponse
from app.core.exceptions import CompanyOwnerOnly, CompanyMembershipForbidden
from app.schemas.company_member import CompanyMemberResponse

from app.core.logger import logger

class CompanyMemberService:

  def __init__(self, repository: CompanyMemberRepository):
    self.repository = repository

  # ===================================================================================
  # Отримати всіх учасників компанії
  # ===================================================================================
  async def get_members(
    self, 
    company_id: UUID, 
    limit: int = 100, 
    offset: int = 0
  ) -> list[CompanyMemberResponse]:
    members = await self.repository.get_all_members_for_current_company(company_id, limit, offset)
    logger.info(f"Fetched members of company {company_id}, limit={limit}, offset={offset}")
    return [CompanyMemberResponse.model_validate(member) for member in members]

  # ===================================================================================
  # Власник компанії видаляє члена
  # ===================================================================================
  async def remove_member(
    self, 
    company_id: UUID, 
    member_id: UUID, 
    current_user: UserDetailResponse
  ):
    # Перевірка, чи current_user є власником компанії
    if not current_user.is_owner_of_company(company_id):
      logger.warning(f"User is not owner of company {company_id}")
      raise CompanyOwnerOnly("Only owners can remove members")
    await self.repository.remove_member(company_id, member_id)
    logger.info(f"Owner removed from company id={company_id} member {member_id}")
    return

  # ===================================================================================
  # Член компанії сам залишає компанію
  # ===================================================================================
  async def leave_company(
    self, 
    company_id: UUID, 
    current_user: UserDetailResponse
  ):
    # Перевірка, що користувач видаляє тільки себе
    if not current_user.is_member_of_company(company_id):
      logger.warning(f"User is not member of company {company_id}")
      raise CompanyMembershipForbidden("You can only leave your own company membership")
    await self.repository.remove_member(company_id, current_user.id)
    logger.info(f"Member leave company {company_id}")
    return
