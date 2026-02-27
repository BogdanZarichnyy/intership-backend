from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.company_member import CompanyMemberRepository
from app.repositories.company import CompanyRepository
from app.models.company_member import CompanyMember, CompanyRole
from app.core.exceptions import CompanyNotFound, CompanyOwnerOnly, CompanyMembershipForbidden
from app.core.logger import logger

class CompanyAdminService:
  def __init__(self, db: AsyncSession):
    self.db = db
    self.member_repo = CompanyMemberRepository(db)
    self.company_repo = CompanyRepository(db)

  async def get_admin(self, company_id: UUID, owner_id: UUID, user_id: UUID):
    company = await self.company_repo.get_company_by_id(company_id)
    if not company:
      logger.warning(f"Company {company_id} not found (user_id={user_id})")
      raise CompanyNotFound()
    if company.owner_id != owner_id:
      logger.warning(f"User {user_id} is not owner company id={company_id}")
      raise CompanyOwnerOnly()
    member = await self.member_repo.get_member(company_id, user_id)
    if not member or member.role != CompanyRole.admin:
      logger.warning(f"User {user_id} is not a member or admin of company {company_id}")
      raise CompanyMembershipForbidden("User is not an admin")
    return member

  async def remove_admin(self, company_id: UUID, owner_id: UUID, user_id: UUID):
    company = await self.company_repo.get_company_by_id(company_id)
    if not company:
      logger.warning(f"Company {company_id} not found (user_id={user_id})")
      raise CompanyNotFound()
    if company.owner_id != owner_id:
      logger.warning(f"User {user_id} is not owner company id={company_id}")
      raise CompanyOwnerOnly()
    member = await self.member_repo.get_member(company_id, user_id)
    if not member or member.role != CompanyRole.admin:
      logger.warning(f"User {user_id} is not a member or admin of company {company_id}")
      raise CompanyMembershipForbidden("User is not an admin")
    await self.member_repo.remove_member(member)

  async def change_member_role(self, company_id: UUID, owner_id: UUID, user_id: UUID, role: CompanyRole) -> CompanyMember:
    company = await self.company_repo.get_company_by_id(company_id)
    if not company:
      logger.warning(f"Company {company_id} not found (user_id={user_id})")
      raise CompanyNotFound()
    if company.owner_id != owner_id:
      logger.warning(f"User {user_id} is not owner company id={company_id}")
      raise CompanyOwnerOnly()
    member = await self.member_repo.get_member(company_id, user_id)
    if not member:
      logger.warning(f"User {user_id} does not exist in this company id={company_id}")
      raise CompanyMembershipForbidden("Member does not exist in this company")
    logger.info(f"Changed role of user {user_id} in company {company_id} from {member.role} to {role} (owner_id_id={owner_id})")
    return await self.member_repo.set_role(member, role)

  async def get_list_admins(self, company_id: UUID, owner_id: UUID):
    company = await self.company_repo.get_company_by_id(company_id)
    if not company:
      logger.warning(f"Company {company_id} not found (user_id={owner_id})")
      raise CompanyNotFound()
    if company.owner_id != owner_id:
      logger.warning(f"User {owner_id} is not owner company id={company_id}")
      raise CompanyOwnerOnly()
    return await self.member_repo.get_all_members_for_current_company(company_id, role=CompanyRole.admin)
