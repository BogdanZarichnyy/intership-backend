from uuid import UUID
from app.core.logger import logger
from app.core.exceptions import CompanyNotFound, CompanyOwnerOnly, CompanyMembershipForbidden
from app.repositories.company_member import CompanyMemberRepository
from app.repositories.company import CompanyRepository
from app.models.company_member import CompanyMember, CompanyRole
from app.models.user import User
from app.schemas.company_member import CompanyAdminsResponse, CompanyMemberResponse

class CompanyAdminService:
  def __init__(self, member_repo: CompanyMemberRepository, company_repo: CompanyRepository):
    self.member_repo = member_repo
    self.company_repo = company_repo

  async def get_list_admins(
    self, 
    company_id: UUID, 
    current_user: User
  ) -> CompanyAdminsResponse:
    company = await self.company_repo.get_company_by_id(company_id)
    if not company:
      logger.warning(f"Company {company_id} not found (user_id={current_user.id})")
      raise CompanyNotFound()
    if company.owner_id != current_user.id:
      logger.warning(f"User {current_user.id} is not owner company id={company_id}")
      raise CompanyOwnerOnly()
    logger.info(f"Fetched member in company id={company_id}")
    result = await self.member_repo.get_all_members_for_current_company(company_id)
    return CompanyAdminsResponse(admins=result)

  async def change_member_role(
    self,
    company_id: UUID,
    user_id: UUID,
    current_user: User,
    role: CompanyRole
  ) -> CompanyMemberResponse:
    company = await self.company_repo.get_company_by_id(company_id)
    if not company:
      logger.warning(f"Company {company_id} not found (user_id={user_id})")
      raise CompanyNotFound()
    if company.owner_id != current_user.id:
      logger.warning(f"User {user_id} is not owner company id={company_id}")
      raise CompanyOwnerOnly()
    member = await self.member_repo.get_member_of_company(company_id, user_id)
    if not member:
      logger.warning(f"User {user_id} does not exist in this company id={company_id}")
      raise CompanyMembershipForbidden("Member does not exist in this company")
    logger.info(f"Changed role of user {user_id} in company {company_id} from {member.role} to {role} (owner_id={current_user.id})")
    result = await self.member_repo.set_role(company_id, user_id, role)
    return CompanyMemberResponse.model_validate(result)

  async def remove_admin(
    self,
    company_id: UUID,
    user_id: UUID,
    current_user: User
  ) -> None:
    company = await self.company_repo.get_company_by_id(company_id)
    if not company:
      logger.warning(f"Company {company_id} not found (user_id={user_id})")
      raise CompanyNotFound()
    if company.owner_id != current_user.id:
      logger.warning(f"User {user_id} is not owner company id={company_id}")
      raise CompanyOwnerOnly()
    member = await self.member_repo.get_member_of_company(company_id, user_id)
    if not member or member.role != CompanyRole.admin:
      logger.warning(f"User {user_id} is not a member or admin of company {company_id}")
      raise CompanyMembershipForbidden("User is not an admin")
    await self.member_repo.remove_member(company_id, user_id)

