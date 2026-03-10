from uuid import UUID
from app.core.logger import logger
from app.core.exceptions import (
  CompanyOwnerOnly,
  CompanyMembershipForbidden,
  CompanyNotFound
)
from app.models.company_member import CompanyRole
from app.repositories.company_member import CompanyMemberRepository
from app.repositories.company import CompanyRepository
from app.models.user import User
from app.schemas.company_member import CompanyMemberResponse

class CompanyMemberService:

  def __init__(
    self,
    member_repo: CompanyMemberRepository,
    company_repo: CompanyRepository
  ):
    self.member_repo = member_repo
    self.company_repo = company_repo

  # ===================================================================================
  # Отримати всіх учасників компанії
  # ===================================================================================
  async def get_members(
    self, 
    company_id: UUID, 
    limit: int = 100, 
    offset: int = 0
  ) -> list[CompanyMemberResponse]:
    members = await self.member_repo.get_all_members_for_current_company(company_id=company_id, limit=limit, offset=offset)
    logger.info(f"Fetched members of company {company_id}, limit={limit}, offset={offset}")
    return [CompanyMemberResponse.model_validate(member) for member in members]

  # ===================================================================================
  # Власник компанії видаляє члена
  # ===================================================================================
  async def remove_member(
    self,
    company_id: UUID,
    member_id: UUID,
    current_user: User
  ) -> None:
    # Перевіряємо що компанія існує
    company = await self.company_repo.get_company_by_id(company_id)
    if not company:
      logger.warning(f"Company not found id={company_id}")
      raise CompanyNotFound()
    # Перевіряємо що поточний користувач є власником цієї компанії
    if company.owner_id != current_user.id:
      logger.warning(f"User {current_user.id} is not owner of company {company_id}")
      raise CompanyOwnerOnly("Only owners can remove members")
    # Перевіряємо що користувач дійсно є членом цієї компанії
    member = await self.member_repo.get_member_of_company(company_id, member_id)
    if not member:
      logger.warning(f"User {member_id} is not a member of company {company_id}")
      raise CompanyMembershipForbidden("User is not a member of this company")
    # Видаляємо
    await self.member_repo.remove_member(company_id, member_id)
    logger.info(f"Owner {current_user.id} removed member {member_id} from company {company_id}")

  # ===================================================================================
  # Член компанії сам залишає компанію
  # ===================================================================================
  async def leave_company(
    self, 
    company_id: UUID,
    member_id: UUID,
    current_user: User
  ) -> None:
    # Перевіряємо що компанія існує
    company = await self.company_repo.get_company_by_id(company_id)
    if not company:
      logger.warning(f"Company not found id={company_id}")
      raise CompanyNotFound()
    # Власник не може залишити компанію
    if company.owner_id == current_user.id:
      logger.warning("Owner cannot leave company without ownership transfer")
      raise CompanyMembershipForbidden("Owner cannot leave their own company")
    # Користувач може видаляти лише самого себе
    if current_user.id != member_id:
      logger.warning(f"User {current_user.id} tried to leave company {company_id} for another user {member_id}")
      raise CompanyMembershipForbidden("You can only leave company for yourself")
    # Перевірка що користувач є членом компанії
    member = await self.member_repo.get_member_of_company(company_id, member_id)
    if not member:
      logger.warning(f"User {member_id} is not a member of company {company_id}")
      raise CompanyMembershipForbidden("You are not a member of this company")
    # Видаляємо тільки самого себе
    await self.member_repo.remove_member(company_id, member_id)
    logger.info(f"User {member_id} left company {company_id}")

  # ===================================================================================
  # Перевірка прав доступу - користувач являється власником чи адміністратором компанії
  # ===================================================================================
  async def check_owner_or_admin(
    self,
    company_id: UUID,
    user_id: UUID
  ) -> None:
    member = await self.member_repo.get_member_of_company(company_id, user_id)
    if not member or member.role != CompanyRole.admin:
      logger.info(f"User {user_id} passed owner/admin check for company {company_id} (admin)")
      return
    company = await self.company_repo.get_company_by_id(company_id)
    if not company:
      logger.warning(f"Company {company_id} not found during owner/admin check")
      raise CompanyNotFound()
    if company.owner_id != user_id:
      logger.warning(f"User {user_id} is neither admin nor owner of company {company_id}")
      raise CompanyMembershipForbidden("User must be admin or owner to perform this action")
    logger.info(f"User {user_id} is company owner of {company_id}")
