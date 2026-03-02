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
  CompanyNotFound,
  InvitationForbidden
)
from app.core.exceptions import CompanyOwnerOnly
from app.core.logger import logger

class CompanyInvitationService:
  def __init__(self, db: AsyncSession):
    self.db = db
    self.invitation_repo = CompanyInvitationRepository(db)
    self.member_repo = CompanyMemberRepository(db)
    self.company_repo = CompanyRepository(db)

  # ==================================================
  # Створення invite/request на приєднання до компанії
  # ==================================================
  async def company_join_initialization(
    self, 
    company: Company, 
    current_user: User, 
    user_id: UUID
  ):
    # Перевірка - хто із авторизованих користувачів ініціює приєднання до компанії
    if current_user.id == company.owner_id:
      # Якщо ініціатор власник компанії (owner company), тоді він запрошує користувача → invite
      invitation = await self.invitation_repo.create_invitation(
        company_id=company.id,
        invited_user_id=user_id,         # Хто приєднується - користувач якому кинули запрошення
        invited_by=current_user.id       # Хто ініціатор - власник компанії сам запросив користувача
      )
      logger.info(f"Owner of company id={company.id} creates invitation to user {current_user.id}")
    else: 
      # Якщо ініціатор користувач (user), тоді він створює запит на приєднання до компанії → request
      invitation = await self.invitation_repo.create_invitation(
        company_id=company.id,
        invited_user_id=current_user.id, # Хто приєднується - користувач який ініціював запит
        invited_by=current_user.id       # Хто ініціатор - сам користувач
      )
      logger.info(f"User creates request to company id={company.id}")
    await self.db.commit()
    logger.info(f"Invitation/request id={invitation.id} created by user {current_user.id}")
    return invitation
  
  # ==============================================================================
  # 1. Користувач отримує список своїх запитів на приєднання до компаній → request
  # ==============================================================================
  async def get_user_requests(
    self,
    user_id: UUID,
    limit,
    offset
  ):
    logger.info(f"Owner fetched all members of himself company limit={limit} offset={offset}")
    return await self.invitation_repo.get_user_requests(user_id, limit, offset)

  # ===========================================================================
  # 2. Користувач отримує список всіх запрошень від власників компаній → invite
  # ===========================================================================
  async def get_user_received_invitations(
    self,
    user_id: UUID,
    limit,
    offset
  ):
    logger.info(f"User fetched all requests to youself of companies limit={limit} offset={offset}")
    return await self.invitation_repo.get_user_received_invitations(user_id, limit, offset)

  # =======================================================================================
  # 3. Власник компанії отримує список всіх запрошених користувачів → invite/request accept
  # =======================================================================================
  async def get_company_invited_users(
    self,
    company_id: UUID,
    current_user: User,
    limit: int,
    offset: int
  ):
    company = await self.company_repo.get_company_by_id(company_id)
    if not company:
      logger.warning(f"Company not found id={company_id}")
      raise CompanyNotFound("Company not found")
    if company.owner_id != current_user.id:
      logger.warning(f"User is not owner of company id={current_user.id}")
      raise CompanyOwnerOnly("Only owners can see invited users")
    return await self.invitation_repo.get_company_invited_users(company_id, current_user.id, limit, offset)

  # ==========================================================================
  # 4. Власник компанії отримує всі заявки на приєднання які в статусі pending
  # ==========================================================================
  async def get_company_membership_requests(
    self,
    company_id: UUID,
    current_user: User,
    limit: int,
    offset: int
  ):
    company = await self.company_repo.get_company_by_id(company_id)
    if not company:
      logger.warning(f"Company not found id={company_id}")
      raise CompanyNotFound("Company not found")
    if company.owner_id != current_user.id:
      logger.warning(f"User is not owner of company id={current_user.id}")
      raise CompanyOwnerOnly("Only owners can see pending membership requests")
    return await self.invitation_repo.get_company_membership_requests(company_id, current_user.id, limit, offset)

  # ===============================================================
  # Підтвердження на приєднання до компанії → invite/request accept
  # ===============================================================
  async def accept_invitation(
    self,
    invitation_id: UUID,
    current_user: User
  ) -> CompanyInvitation:
    invitation = await self.invitation_repo.get_invitation_by_id(invitation_id)
    if not invitation:
      logger.warning(f"Invitation id={invitation_id} not found")
      raise InvitationNotFound()
    if invitation.status != InvitationStatus.pending:
      logger.warning(f"Invitation already processed")
      raise InvitationAlreadyProcessed()
    company = await self.company_repo.get_company_by_id(invitation.company_id)
    if not company:
      logger.warning(f"Company not found id={invitation.company_id}")
      raise CompanyNotFound("Company not found")
    # owner invite → accept user
    if invitation.invited_by == company.owner_id:
      if invitation.invited_user_id != current_user.id:
        logger.warning("Not your invitation")
        raise InvitationForbidden("Not your invitation")
    # user request → owner accept
    else:
      if company.owner_id != current_user.id:
        logger.warning("Only owner can accept requests for invitations")
        raise InvitationForbidden("Only owner can accept requests for invitations")
    # Змінюємо статус заявки - підтверджуємо приєднання до компанії
    await self.invitation_repo.update_status(invitation, InvitationStatus.accepted)
    # Додаємо користувача в члени компанії
    await self.member_repo.add_member(invitation.company_id, invitation.invited_user_id)
    await self.db.commit()
    logger.info(f"Invitation {invitation.id} accepted by user {current_user.id}")
    return invitation
  
  # ===================================================================================
  # Власник компанії відхилив запит на приєднання до компанії →  invite/request decline
  # ===================================================================================
  async def decline_invitation(
    self,
    invitation_id: UUID,
    current_user: User
  ) -> CompanyInvitation:
    invitation = await self.invitation_repo.get_invitation_by_id(invitation_id)
    if not invitation:
      logger.warning(f"Invitation id={invitation_id} not found")
      raise InvitationNotFound()
    company = await self.company_repo.get_company_by_id(invitation.company_id)
    if not company:
      logger.warning(f"Company not found id={invitation.company_id}")
      raise CompanyNotFound("Company not found")
    # owner invite → accept user
    if invitation.invited_by == company.owner_id:
      if invitation.invited_user_id != current_user.id:
        logger.warning("Not your invitation")
        raise InvitationForbidden("Not your invitation")
    # user request → owner accept
    else:
      if company.owner_id != current_user.id:
        raise InvitationForbidden("Only owner can decline requests for invitations")
    # Змінюємо статус заявки
    await self.invitation_repo.update_status(invitation, InvitationStatus.declined)
    await self.db.commit()
    logger.info(f"Invitation {invitation.id} declined by user {current_user.id}")
    return invitation

  # =============================================================================
  # Користувач сам відмінив свій запит на приєднання до компанії → request cancel
  # =============================================================================
  async def cancel_invitation(
    self, 
    invitation_id: UUID, 
    current_user: User
  ) -> CompanyInvitation:
    invitation = await self.invitation_repo.get_invitation_by_id(invitation_id)
    if not invitation:
      logger.warning(f"Invitation id={invitation_id} not found")
      raise InvitationNotFound()
    company = await self.company_repo.get_company_by_id(invitation.company_id)
    if not company:
      logger.warning(f"Company not found id={invitation.company_id}")
      raise CompanyNotFound("Company not found")
    is_owner = company.owner_id == current_user.id
    is_target_user = invitation.invited_user_id == current_user.id
    if not is_owner and not is_target_user:
      logger.warning("Not allowed to cancel this invitation")
      raise InvitationForbidden("Not allowed to cancel this invitation")
    # Змінюємо статус заявки
    await self.invitation_repo.update_status(invitation, InvitationStatus.cancelled)
    await self.db.commit()
    logger.info(f"Invitation {invitation.id} cancelled by user {current_user.id}")
    return invitation
