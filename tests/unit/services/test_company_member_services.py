import pytest
from unittest.mock import AsyncMock
from uuid import uuid4
from datetime import datetime, timezone
from app.services.company_member import CompanyMemberService
from app.models.company_member import CompanyRole
from app.models.user import User
from app.core.exceptions import (
    CompanyNotFound,
    CompanyOwnerOnly,
    CompanyMembershipForbidden
)


@pytest.fixture
def member_repo():
    return AsyncMock()


@pytest.fixture
def company_repo():
    return AsyncMock()


@pytest.fixture
def service(member_repo, company_repo):
    return CompanyMemberService(member_repo, company_repo)


@pytest.fixture
def user():
    u = User()
    u.id = uuid4()
    return u


def make_company(owner_id):
    return type("Company", (), {"owner_id": owner_id})()


def make_member(company_id, user_id, role=CompanyRole.member):
    return type("Member", (), {
        "company_id": company_id,
        "member_id": user_id,
        "role": role,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    })()


# -------------------------
# get_members
# -------------------------

@pytest.mark.asyncio
async def test_get_members(service, member_repo):
    member_repo.get_all_members_for_current_company.return_value = [
        make_member(uuid4(), uuid4())
    ]

    result = await service.get_members(uuid4())

    assert isinstance(result, list)


# -------------------------
# remove_member
# -------------------------

@pytest.mark.asyncio
async def test_remove_member_company_not_found(service, company_repo, user):
    company_repo.get_company_by_id.return_value = None

    with pytest.raises(CompanyNotFound):
        await service.remove_member(uuid4(), uuid4(), user)


@pytest.mark.asyncio
async def test_remove_member_not_owner(service, company_repo, user):
    company_repo.get_company_by_id.return_value = make_company(uuid4())

    with pytest.raises(CompanyOwnerOnly):
        await service.remove_member(uuid4(), uuid4(), user)


@pytest.mark.asyncio
async def test_remove_member_not_member(service, company_repo, member_repo, user):
    company_repo.get_company_by_id.return_value = make_company(user.id)
    member_repo.get_member_of_company.return_value = None

    with pytest.raises(CompanyMembershipForbidden):
        await service.remove_member(uuid4(), uuid4(), user)


@pytest.mark.asyncio
async def test_remove_member_success(service, company_repo, member_repo, user):
    company_repo.get_company_by_id.return_value = make_company(user.id)
    member_repo.get_member_of_company.return_value = make_member(uuid4(), uuid4())

    await service.remove_member(uuid4(), uuid4(), user)

    member_repo.remove_member.assert_called_once()


# -------------------------
# leave_company
# -------------------------

@pytest.mark.asyncio
async def test_leave_company_owner_forbidden(service, company_repo, user):
    company_repo.get_company_by_id.return_value = make_company(user.id)

    with pytest.raises(CompanyMembershipForbidden):
        await service.leave_company(uuid4(), user.id, user)


@pytest.mark.asyncio
async def test_leave_company_wrong_user(service, company_repo, user):
    company_repo.get_company_by_id.return_value = make_company(uuid4())

    with pytest.raises(CompanyMembershipForbidden):
        await service.leave_company(uuid4(), uuid4(), user)


@pytest.mark.asyncio
async def test_leave_company_success(service, company_repo, member_repo, user):
    company_repo.get_company_by_id.return_value = make_company(uuid4())
    member_repo.get_member_of_company.return_value = make_member(uuid4(), user.id)

    await service.leave_company(uuid4(), user.id, user)

    member_repo.remove_member.assert_called_once()


# -------------------------
# check_owner_or_admin
# -------------------------

@pytest.mark.asyncio
async def test_owner(service, company_repo, user):
    company_repo.get_company_by_id.return_value = make_company(user.id)

    result = await service.check_owner_or_admin(uuid4(), user.id)

    assert result is None


@pytest.mark.asyncio
async def test_admin(service, company_repo, member_repo, user):
    company_repo.get_company_by_id.return_value = make_company(uuid4())
    member_repo.get_member_of_company.return_value = make_member(
        uuid4(), user.id, CompanyRole.admin
    )

    result = await service.check_owner_or_admin(uuid4(), user.id)

    assert result is None


@pytest.mark.asyncio
async def test_forbidden(service, company_repo, member_repo, user):
    company_repo.get_company_by_id.return_value = make_company(uuid4())
    member_repo.get_member_of_company.return_value = make_member(
        uuid4(), user.id, CompanyRole.member
    )

    with pytest.raises(CompanyMembershipForbidden):
        await service.check_owner_or_admin(uuid4(), user.id)
