from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.company import Company
from app.models.user import User
from app.models.company_invitation import InvitationStatus, CompanyInvitation
from app.repositories.company_invitation import CompanyInvitationRepository
from app.repositories.company_member import CompanyMemberRepository
from app.repositories.company import CompanyRepository
from app.core.exceptions import (
  InvitationNotFound, 
  InvitationAlreadyProcessed, 
  InvitationForbidden, 
  CompanyNotFound
)
from app.core.logger import logger

class CompanyInvitationService:
  def __init__(self, db: AsyncSession):
    self.db = db
    self.invitation_repo = CompanyInvitationRepository(db)
    self.member_repo = CompanyMemberRepository(db)
    self.company_repo = CompanyRepository(db)

  async def company_join_initialization(
    self, 
    company: Company, 
    current_user: User, 
    target_user_id: UUID
  ):
    logger.info(f"User {current_user.id} creates invitation/request to company {company.id}")
    if current_user.id == company.owner_id:
      # Власник запрошує користувача, якщо ініціатор owner company → invite
      invitation = await self.invitation_repo.create_invitation(
        company_id=company.id,
        invited_user_id=target_user_id,
        invited_by=current_user.id
      )
    else: # Користувач створює запит на приєднання
      # якщо ініціатор user → request
      invitation = await self.invitation_repo.create_invitation(
        company_id=company.id,
        invited_user_id=current_user.id,
        invited_by=current_user.id
      )
    await self.db.commit()
    logger.info(f"Invitation {invitation.id} created by user {current_user.id}")
    return invitation
  
  # 1. USER → список своїх membership requests
  async def get_user_requests(
    self,
    user_id: UUID,
    limit,
    offset
  ):
    return await self.invitation_repo.get_user_requests(
      user_id,
      limit,
      offset
    )

  # 2. USER → список received invitations
  async def get_user_received_invitations(
    self,
    user_id: UUID,
    limit,
    offset
  ):
    return await self.invitation_repo.get_user_received_invitations(
      user_id,
      limit,
      offset
    )

  # 3. OWNER → invited users
  async def get_company_invited_users(
    self,
    company_id: UUID,
    current_user: User,
    limit: int,
    offset: int
  ):
    company = await self.company_repo.get_company_by_id(company_id)
    if not company:
      raise CompanyNotFound("Company not found")
    if company.owner_id != current_user.id:
      raise InvitationForbidden()
    return await self.invitation_repo.get_company_invited_users(
      company_id,
      current_user.id,
      limit,
      offset
    )

  # 4. OWNER → pending membership requests
  async def get_company_membership_requests(
    self,
    company_id: UUID,
    current_user: User,
    limit: int,
    offset: int
  ):
    company = await self.company_repo.get_company_by_id(company_id)
    if not company:
      raise CompanyNotFound("Company not found")
    if company.owner_id != current_user.id:
      raise InvitationForbidden()
    return await self.invitation_repo.get_company_membership_requests(
      company_id,
      current_user.id,
      limit,
      offset
    )

  async def accept_invitation(
    self,
    invitation_id: UUID,
    current_user: User
  ) -> CompanyInvitation:
    invitation = await self.invitation_repo.get_invitation_by_id(invitation_id)
    if not invitation:
      raise InvitationNotFound()
    if invitation.status != InvitationStatus.pending:
      raise InvitationAlreadyProcessed()
    company = await self.company_repo.get_company_by_id(invitation.company_id)
    if not company:
      raise CompanyNotFound("Company not found")
    # owner invite → accept user
    if invitation.invited_by == company.owner_id:
      if invitation.invited_user_id != current_user.id:
        raise InvitationForbidden("Not your invitation")
    # user request → owner accept
    else:
      if company.owner_id != current_user.id:
        raise InvitationForbidden("Only owner can accept requests for invitations")
    # Update status via repository
    await self.invitation_repo.update_status(invitation, InvitationStatus.accepted)
    # Додаємо користувача в члени компанії
    await self.member_repo.add_member(
      invitation.company_id,
      invitation.invited_user_id
    )
    await self.db.commit()
    logger.info(f"Invitation {invitation.id} accepted by user {current_user.id}")
    return invitation
  
  async def decline_invitation(
    self,
    invitation_id: UUID,
    current_user: User
  ) -> CompanyInvitation:
    invitation = await self.invitation_repo.get_invitation_by_id(invitation_id)
    if not invitation:
      raise InvitationNotFound()
    company = await self.company_repo.get_company_by_id(invitation.company_id)
    if not company:
      raise CompanyNotFound("Company not found")
    # owner invite → accept user
    if invitation.invited_by == company.owner_id:
      if invitation.invited_user_id != current_user.id:
        raise InvitationForbidden("Not your invitation")
    # user request → owner accept
    else:
      if company.owner_id != current_user.id:
        raise InvitationForbidden("Only owner can decline requests for invitations")
    # Update status via repository
    await self.invitation_repo.update_status(invitation, InvitationStatus.declined)
    await self.db.commit()
    logger.info(f"Invitation {invitation.id} declined by user {current_user.id}")
    return invitation

  async def cancel_invitation(
    self, 
    invitation_id: UUID, 
    current_user: User
  ) -> CompanyInvitation:
    invitation = await self.invitation_repo.get_invitation_by_id(invitation_id)
    if not invitation:
      raise InvitationNotFound()
    company = await self.company_repo.get_company_by_id(invitation.company_id)
    if not company:
      raise CompanyNotFound("Company not found")
    is_owner = company.owner_id == current_user.id
    is_target_user = invitation.invited_user_id == current_user.id
    if not is_owner and not is_target_user:
      raise InvitationForbidden("Not allowed to cancel this invitation")
    # Update status via repository
    await self.invitation_repo.update_status(invitation, InvitationStatus.cancelled)
    await self.db.commit()
    logger.info(f"Invitation {invitation.id} cancelled by user {current_user.id}")
    return invitation
