from uuid import UUID
from fastapi import APIRouter, Depends, Query

from app.schemas.company_invitation import InvitationResponse
from app.services.company_invitation import CompanyInvitationService
from app.core.dependencies import get_current_user, get_invitation_service
from app.schemas.user import UserDetailResponse

router = APIRouter(tags=["company-invitations"])

# Створення запиту на членство в компанію
@router.post(
  "/{company_id}/{user_id}", 
  response_model=InvitationResponse
)
async def invite_user(
  company_id: UUID,
  user_id: UUID,
  service: CompanyInvitationService = Depends(get_invitation_service),
  current_user=Depends(get_current_user)
):
  return await service.company_join_initialization(company_id, current_user, user_id)

# 1 user requests
@router.get("/my-requests")
async def get_my_requests(
  limit: int = Query(50),
  offset: int = Query(0),
  service: CompanyInvitationService = Depends(get_invitation_service),
  current_user: UserDetailResponse = Depends(get_current_user),
):
  return await service.get_user_requests(
    current_user.id,
    limit,
    offset
  )

# 2 received invitations
@router.get("/my-invitations")
async def get_my_invitations(
  limit: int = Query(50),
  offset: int = Query(0),
  service: CompanyInvitationService = Depends(get_invitation_service),
  current_user: UserDetailResponse = Depends(get_current_user),
):
  return await service.get_user_received_invitations(
    current_user.id,
    limit,
    offset
  )

# 3 owner invited users
@router.get("/company/{company_id}/invited")
async def get_company_invited(
  company_id: UUID,
  limit: int = Query(50),
  offset: int = Query(0),
  service: CompanyInvitationService = Depends(get_invitation_service),
  current_user: UserDetailResponse = Depends(get_current_user),
):
  return await service.get_company_invited_users(
    company_id,
    current_user,
    limit,
    offset
  )

# 4 owner membership requests
@router.get("/company/{company_id}/requests")
async def get_company_requests(
  company_id: UUID,
  limit: int = Query(50),
  offset: int = Query(0),
  service: CompanyInvitationService = Depends(get_invitation_service),
  current_user: UserDetailResponse = Depends(get_current_user),
):
  return await service.get_company_membership_requests(
    company_id,
    current_user,
    limit,
    offset
  )

# Підтвердити/прийняти запрошення може як і Owner так і User відповідно
@router.put(
  "/{invitation_id}/accept", 
  response_model=InvitationResponse
)
async def accept_invitation(
  invitation_id: UUID,
  service: CompanyInvitationService = Depends(get_invitation_service),
  current_user=Depends(get_current_user)
):
  invitation = await service.accept_invitation(invitation_id, current_user)
  return invitation

# Відхилити запрошення може тільки Owner, якщо ініціатором був User
@router.put(
  "/{invitation_id}/decline", 
  response_model=InvitationResponse
)
async def decline_invitation(
  invitation_id: UUID,
  service: CompanyInvitationService = Depends(get_invitation_service),
  current_user=Depends(get_current_user)
):
  invitation = await service.decline_invitation(invitation_id, current_user)
  return invitation

# Відмінити запрошення може як і Owner так і User
@router.put(
  "/{invitation_id}/cancel", 
  response_model=InvitationResponse
)
async def cancel_invitation(
  invitation_id: UUID,
  service: CompanyInvitationService = Depends(get_invitation_service),
  current_user=Depends(get_current_user)
):
  invitation = await service.cancel_invitation(invitation_id, current_user)
  return invitation
