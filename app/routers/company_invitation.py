from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from app.core.dependencies import get_current_user, get_invitation_service
from app.models.user import User
from app.schemas.company_invitation import InvitationResponse
from app.services.company_invitation import CompanyInvitationService

router = APIRouter(tags=["company-invitations"])

# Створення запиту на членство в компанію
@router.post(
  "/{company_id}", 
  response_model=InvitationResponse,
  status_code=status.HTTP_201_CREATED
)
async def invite_user(
  company_id: UUID,
  user_id: UUID | None = None,
  service: CompanyInvitationService = Depends(get_invitation_service),
  current_user: User = Depends(get_current_user)
) -> InvitationResponse:
  user_id = user_id or current_user.id
  return await service.company_join_initialization(company_id, user_id, current_user)

# 1 user requests
@router.get(
  "/my-requests",
  status_code=status.HTTP_200_OK
)
async def get_my_requests(
  limit: int = Query(50),
  offset: int = Query(0),
  service: CompanyInvitationService = Depends(get_invitation_service),
  current_user: User = Depends(get_current_user),
) -> list[InvitationResponse]:
  return await service.get_user_requests(current_user, limit, offset)

# 2 received invitations
@router.get(
  "/my-invitations",
  status_code=status.HTTP_200_OK
)
async def get_my_invitations(
  limit: int = Query(50),
  offset: int = Query(0),
  service: CompanyInvitationService = Depends(get_invitation_service),
  current_user: User = Depends(get_current_user),
) -> list[InvitationResponse]:
  return await service.get_user_received_invitations(current_user, limit, offset)

# 3 owner invited users
@router.get(
  "/{company_id}/invited",
  status_code=status.HTTP_200_OK
)
async def get_company_invited(
  company_id: UUID,
  limit: int = Query(50),
  offset: int = Query(0),
  service: CompanyInvitationService = Depends(get_invitation_service),
  current_user: User = Depends(get_current_user),
) -> list[InvitationResponse]:
  return await service.get_company_invited_users(company_id, current_user, limit, offset)

# 4 owner membership requests
@router.get(
  "/{company_id}/requests",
  status_code=status.HTTP_200_OK
)
async def get_company_requests(
  company_id: UUID,
  limit: int = Query(50),
  offset: int = Query(0),
  service: CompanyInvitationService = Depends(get_invitation_service),
  current_user: User = Depends(get_current_user),
) -> list[InvitationResponse]:
  return await service.get_company_membership_requests(company_id, current_user, limit, offset)

# Підтвердження запрошення на приєднання до компанії
@router.patch(
  "/{invitation_id}/accept", 
  response_model=InvitationResponse,
  status_code=status.HTTP_200_OK
)
async def accept_invitation(
  invitation_id: UUID,
  service: CompanyInvitationService = Depends(get_invitation_service),
  current_user: User = Depends(get_current_user)
) -> InvitationResponse:
  return await service.accept_invitation(invitation_id, current_user)

# Відхилити заявку на приєднання до компанії може тільки власник компанії
@router.patch(
  "/{invitation_id}/decline", 
  response_model=InvitationResponse,
  status_code=status.HTTP_200_OK
)
async def decline_invitation(
  invitation_id: UUID,
  service: CompanyInvitationService = Depends(get_invitation_service),
  current_user: User = Depends(get_current_user)
) -> InvitationResponse:
  return await service.decline_invitation(invitation_id, current_user)

# Відмінити свою заявку на приєднання до компанії може тільки сам користувач
@router.patch(
  "/{invitation_id}/cancel", 
  response_model=InvitationResponse,
  status_code=status.HTTP_200_OK
)
async def cancel_invitation(
  invitation_id: UUID,
  service: CompanyInvitationService = Depends(get_invitation_service),
  current_user: User = Depends(get_current_user)
) -> InvitationResponse:
  return await service.cancel_invitation(invitation_id, current_user)
