from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.company_invitation import InvitationResponse
from app.models.company import Company
from app.models.user import User
from app.models.company_invitation import InvitationStatus
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
    company_id: UUID,
    user_id: UUID,
    current_user: User
  ):
    company: Company = await self.company_repo.get_company_by_id(company_id)
    if not company:
      logger.warning(f"Company not found id={company_id}")
      raise CompanyNotFound()
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
      raise CompanyNotFound()
    if company.owner_id != current_user.id:
      logger.warning(f"User is not owner of company id={current_user.id}")
      raise CompanyOwnerOnly()
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
      raise CompanyNotFound()
    if company.owner_id != current_user.id:
      logger.warning(f"User is not owner of company id={current_user.id}")
      raise CompanyOwnerOnly()
    return await self.invitation_repo.get_company_membership_requests(company_id, current_user.id, limit, offset)

  # ===============================================================
  # Підтвердження на приєднання до компанії → invite/request accept
  # ===============================================================
  async def accept_invitation(
    self,
    invitation_id: UUID,
    current_user: User
  ) -> InvitationResponse:
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
      raise CompanyNotFound()
    # Логіка підтвердження:
    # 1) Власник компанії
    if current_user.id == company.owner_id:
      # Власник може підтверджувати всі заявки, які надійшли в його компанію
      allowed = True
    # 2) Користувач, який подав заявку
    elif current_user.id == invitation.invited_user_id:
      # Користувач може підтвердити лише свої власні заявки
      # Перевіряємо, що ініціатором не був власник компанії або інший користувач
      if invitation.invited_by == company.owner_id:
        # Немає права підтверджувати запрошення від власника (invite)
        allowed = False
      else:
        allowed = True
    else:
      allowed = False
    if not allowed:
      logger.warning(f"User {current_user.id} cannot accept this invitation {invitation.id}")
      raise InvitationForbidden("You are not allowed to accept this invitation")
    # Змінюємо статус заявки на accepted
    await self.invitation_repo.update_status(invitation, InvitationStatus.accepted)
    # Перевіряємо чи користувач вже є членом компанії, оскільки заявок на вступ може бути декілька - тобто: 
    # заявку може кинути як і власник компанії користувачу, так і сам користувач в компанію. Також потрібно 
    # врахувати момент що старі по часу заявки можна відхиляти, а нові можна підтверджувати на вступ. Таким 
    # чином у нас буде історія заявок на вступ, з різними часовими мітками та часом обробки цих заявок.
    existing_member = await self.member_repo.get_member_of_company(invitation.company_id, invitation.invited_user_id)
    if existing_member:
      logger.info(f"User {invitation.invited_user_id} is already a member of company {invitation.company_id}")
    else:
      # Додаємо користувача в члени компанії якщо такого запису ще немає в таблиці
      await self.member_repo.add_member(invitation.company_id, invitation.invited_user_id)
    await self.db.commit()
    await self.db.refresh(invitation)
    logger.info(f"Invitation {invitation.id} accepted by user {current_user.id}")
    return InvitationResponse(
      id=invitation.id,
      company_id=invitation.company_id,
      invited_user_id=invitation.invited_user_id,
      invited_by=invitation.invited_by,
      status=invitation.status,
      created_at=invitation.created_at,
      updated_at=invitation.updated_at
    )

  # ===================================================================================
  # Власник компанії відхилив запит на приєднання → invite/request decline
  # ===================================================================================
  async def decline_invitation(
    self,
    invitation_id: UUID,
    current_user: User
  ) -> InvitationResponse:
    invitation = await self.invitation_repo.get_invitation_by_id(invitation_id)
    if not invitation:
      logger.warning(f"Invitation id={invitation_id} not found")
      raise InvitationNotFound()
    company = await self.company_repo.get_company_by_id(invitation.company_id)
    if not company:
      logger.warning(f"Company not found id={invitation.company_id}")
      raise CompanyNotFound()
    # Відхиляти може тільки власник компанії
    if company.owner_id != current_user.id:
      logger.warning("Only owner can decline invitations or requests")
      raise InvitationForbidden("Only owner can decline invitations or requests")
    await self.invitation_repo.update_status(invitation, InvitationStatus.declined)
    await self.db.commit()
    await self.db.refresh(invitation)
    logger.info(f"Invitation {invitation.id} declined by owner {current_user.id}")
    return InvitationResponse(
      id=invitation.id,
      company_id=invitation.company_id,
      invited_user_id=invitation.invited_user_id,
      invited_by=invitation.invited_by,
      status=invitation.status,
      created_at=invitation.created_at,
      updated_at=invitation.updated_at
    )

  # =============================================================================
  # Користувач сам відмінив свій запит → request cancel
  # =============================================================================
  async def cancel_invitation(
    self, 
    invitation_id: UUID, 
    current_user: User
  ) -> InvitationResponse:
    invitation = await self.invitation_repo.get_invitation_by_id(invitation_id)
    if not invitation:
      logger.warning(f"Invitation id={invitation_id} not found")
      raise InvitationNotFound()
    company = await self.company_repo.get_company_by_id(invitation.company_id)
    if not company:
      logger.warning(f"Company not found id={invitation.company_id}")
      raise CompanyNotFound()
    # Скасувати може тільки користувач, який подав заявку
    if invitation.invited_user_id != current_user.id:
      logger.warning("Only the requesting user can cancel their invitation")
      raise InvitationForbidden("Only the requesting user can cancel their invitation")
    await self.invitation_repo.update_status(invitation, InvitationStatus.cancelled)
    await self.db.commit()
    await self.db.refresh(invitation)
    logger.info(f"Invitation {invitation.id} cancelled by user {current_user.id}")
    return InvitationResponse(
      id=invitation.id,
      company_id=invitation.company_id,
      invited_user_id=invitation.invited_user_id,
      invited_by=invitation.invited_by,
      status=invitation.status,
      created_at=invitation.created_at,
      updated_at=invitation.updated_at
    )
