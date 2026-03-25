import pytest
from unittest.mock import AsyncMock
from uuid import uuid4
from datetime import datetime, timezone
from app.services.company_invitation import CompanyInvitationService
from app.models.company import Company
from app.models.company_invitation import InvitationStatus
from app.models.user import User
from app.core.exceptions import (
    CompanyNotFound,
    CompanyOwnerOnly,
    InvitationNotFound,
    InvitationAlreadyProcessed,
    InvitationForbidden
)


@pytest.fixture
def invitation_repo():
    return AsyncMock()

@pytest.fixture
def member_repo():
    return AsyncMock()

@pytest.fixture
def company_repo():
    return AsyncMock()

@pytest.fixture
def service(invitation_repo, member_repo, company_repo):
    return CompanyInvitationService(invitation_repo, member_repo, company_repo)

@pytest.fixture
def user():
    u = User()
    u.id = uuid4()
    return u


def make_company(owner_id):
    return Company(owner_id=owner_id)

def make_invitation(status=InvitationStatus.pending):
    return type("Invitation", (), {
        "id": uuid4(),
        "company_id": uuid4(),
        "invited_user_id": uuid4(),
        "invited_by": uuid4(),
        "status": status,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    })()

def mock_inv(status=..., **overrides):
  return type("Invitation", (), {
    "id": uuid4(),
    "company_id": uuid4(),
    "invited_user_id": uuid4(),
    "invited_by": uuid4(),
    "status": status,
    "created_at": datetime.now(timezone.utc),
    "updated_at": datetime.now(timezone.utc),
    **overrides
  })()

# -------------------------
# company_join_initialization
# -------------------------

@pytest.mark.asyncio
async def test_join_company_not_found(service, company_repo, user):
    company_repo.get_company_by_id.return_value = None

    with pytest.raises(CompanyNotFound):
        await service.company_join_initialization(uuid4(), uuid4(), user)


@pytest.mark.asyncio
async def test_join_company_owner_flow(service, company_repo, invitation_repo, user):
    company_repo.get_company_by_id.return_value = Company(owner_id=user.id)
    invitation_repo.create_invitation.return_value = make_invitation()

    result = await service.company_join_initialization(uuid4(), uuid4(), user)

    assert result is not None


# -------------------------
# get_user_requests
# -------------------------

@pytest.mark.asyncio
async def test_get_user_requests(service, invitation_repo, user):
    invitation_repo.get_user_requests.return_value = []

    result = await service.get_user_requests(user, 10, 0)

    assert result == []


# -------------------------
# get_user_received_invitations
# -------------------------

@pytest.mark.asyncio
async def test_get_user_received(service, invitation_repo, user):
    invitation_repo.get_user_received_invitations.return_value = []

    result = await service.get_user_received_invitations(user, 10, 0)

    assert result == []


# -------------------------
# get_company_invited_users
# -------------------------

@pytest.mark.asyncio
async def test_company_invited_not_owner(service, company_repo, user):
    company_repo.get_company_by_id.return_value = Company(owner_id=uuid4())

    with pytest.raises(CompanyOwnerOnly):
        await service.get_company_invited_users(uuid4(), user, 10, 0)


# -------------------------
# accept_invitation
# -------------------------

@pytest.mark.asyncio
async def test_accept_invitation_not_found(service, invitation_repo, user):
    invitation_repo.get_invitation_by_id.return_value = None

    with pytest.raises(InvitationNotFound):
        await service.accept_invitation(uuid4(), user)


@pytest.mark.asyncio
async def test_accept_invitation_already_processed(service, invitation_repo, user):
    inv = make_invitation(status=InvitationStatus.accepted)
    invitation_repo.get_invitation_by_id.return_value = inv

    with pytest.raises(InvitationAlreadyProcessed):
        await service.accept_invitation(inv.id, user)


@pytest.mark.asyncio
async def test_accept_invitation_success(service, invitation_repo, company_repo, member_repo, user):
    inv = make_invitation()
    invitation_repo.get_invitation_by_id.return_value = inv
    company_repo.get_company_by_id.return_value = Company(owner_id=uuid4())

    member_repo.get_member_of_company.return_value = None

    invitation_repo.update_status.return_value = inv

    result = await service.accept_invitation(inv.id, user)

    assert result is not None


# -------------------------
# decline_invitation
# -------------------------

@pytest.mark.asyncio
async def test_decline_not_owner(service, invitation_repo, company_repo, user):
    inv = make_invitation()

    invitation_repo.get_invitation_by_id.return_value = inv

    company = Company(owner_id=user.id)
    company_repo.get_company_by_id.return_value = company

    # FIX: важливо змокати результат update_status
    invitation_repo.update_status.return_value = make_invitation(status=InvitationStatus.declined)

    result = await service.decline_invitation(inv.id, user)

    assert result is not None


# -------------------------
# cancel_invitation
# -------------------------

@pytest.mark.asyncio
async def test_cancel_not_owner(service, invitation_repo, company_repo, user):
    inv = make_invitation()
    inv.invited_user_id = uuid4()

    invitation_repo.get_invitation_by_id.return_value = inv
    company_repo.get_company_by_id.return_value = Company(owner_id=uuid4())

    with pytest.raises(InvitationForbidden):
        await service.cancel_invitation(inv.id, user)
