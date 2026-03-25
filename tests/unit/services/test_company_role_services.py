import pytest
from unittest.mock import AsyncMock
from uuid import uuid4
from datetime import datetime, timezone
from app.services.company_role import CompanyAdminService
from app.models.company_member import CompanyRole
from app.models.user import User
from app.core.exceptions import CompanyNotFound, CompanyOwnerOnly, CompanyMembershipForbidden
from app.schemas.company_member import CompanyMemberResponse

@pytest.fixture
def member_repo():
    return AsyncMock()

@pytest.fixture
def company_repo():
    return AsyncMock()

@pytest.fixture
def service(member_repo, company_repo):
    return CompanyAdminService(member_repo, company_repo)

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

# =======================
# get_list_admins
# =======================
@pytest.mark.asyncio
async def test_get_list_admins_not_found(service, company_repo, user):
    company_repo.get_company_by_id.return_value = None
    with pytest.raises(CompanyNotFound):
        await service.get_list_admins(uuid4(), user)

@pytest.mark.asyncio
async def test_get_list_admins_not_owner(service, company_repo, user):
    company_repo.get_company_by_id.return_value = make_company(uuid4())
    with pytest.raises(CompanyOwnerOnly):
        await service.get_list_admins(uuid4(), user)

@pytest.mark.asyncio
async def test_get_list_admins_success(service, company_repo, member_repo, user):
    company_repo.get_company_by_id.return_value = make_company(user.id)
    member_repo.get_all_members_for_current_company.return_value = [make_member(uuid4(), uuid4(), CompanyRole.admin)]
    result = await service.get_list_admins(uuid4(), user)
    assert hasattr(result, "admins")
    assert len(result.admins) == 1

# =======================
# change_member_role
# =======================
@pytest.mark.asyncio
async def test_change_member_role_company_not_found(service, company_repo, user):
    company_repo.get_company_by_id.return_value = None
    with pytest.raises(CompanyNotFound):
        await service.change_member_role(uuid4(), uuid4(), user, CompanyRole.admin)

@pytest.mark.asyncio
async def test_change_member_role_not_owner(service, company_repo, user):
    company_repo.get_company_by_id.return_value = make_company(uuid4())
    with pytest.raises(CompanyOwnerOnly):
        await service.change_member_role(uuid4(), uuid4(), user, CompanyRole.admin)

@pytest.mark.asyncio
async def test_change_member_role_member_not_found(service, company_repo, member_repo, user):
    company_repo.get_company_by_id.return_value = make_company(user.id)
    member_repo.get_member_of_company.return_value = None
    with pytest.raises(CompanyMembershipForbidden):
        await service.change_member_role(uuid4(), uuid4(), user, CompanyRole.admin)

@pytest.mark.asyncio
async def test_change_member_role_success(service, company_repo, member_repo, user):
    company_repo.get_company_by_id.return_value = make_company(user.id)
    member_repo.get_member_of_company.return_value = make_member(uuid4(), uuid4(), CompanyRole.member)
    member_repo.set_role.return_value = make_member(uuid4(), uuid4(), CompanyRole.admin)
    result = await service.change_member_role(uuid4(), uuid4(), user, CompanyRole.admin)
    assert isinstance(result, CompanyMemberResponse)

# =======================
# remove_admin
# =======================
@pytest.mark.asyncio
async def test_remove_admin_company_not_found(service, company_repo, user):
    company_repo.get_company_by_id.return_value = None
    with pytest.raises(CompanyNotFound):
        await service.remove_admin(uuid4(), uuid4(), user)

@pytest.mark.asyncio
async def test_remove_admin_not_owner(service, company_repo, user):
    company_repo.get_company_by_id.return_value = make_company(uuid4())
    with pytest.raises(CompanyOwnerOnly):
        await service.remove_admin(uuid4(), uuid4(), user)

@pytest.mark.asyncio
async def test_remove_admin_not_admin(service, company_repo, member_repo, user):
    company_repo.get_company_by_id.return_value = make_company(user.id)
    member_repo.get_member_of_company.return_value = make_member(uuid4(), uuid4(), CompanyRole.member)
    with pytest.raises(CompanyMembershipForbidden):
        await service.remove_admin(uuid4(), uuid4(), user)

@pytest.mark.asyncio
async def test_remove_admin_success(service, company_repo, member_repo, user):
    company_repo.get_company_by_id.return_value = make_company(user.id)
    member_repo.get_member_of_company.return_value = make_member(uuid4(), uuid4(), CompanyRole.admin)
    await service.remove_admin(uuid4(), uuid4(), user)
    member_repo.remove_member.assert_called_once()
