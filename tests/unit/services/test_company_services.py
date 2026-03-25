import pytest
from unittest.mock import AsyncMock
from uuid import uuid4
from datetime import datetime, timezone
from app.services.company import CompanyService
from app.models.user import User
from app.models.company import Company
from app.schemas.company import CompanyCreateRequest, CompanyUpdateRequest
from app.core.exceptions import CompanyNotFound, CompanyForbidden


@pytest.fixture
def repo():
    return AsyncMock()


@pytest.fixture
def service(repo):
    return CompanyService(repo)


@pytest.fixture
def user():
    u = User()
    u.id = uuid4()
    return u


def make_company(owner_id, company_id=None, visible=True):
    return Company(
        id=company_id or uuid4(),
        owner_id=owner_id,
        is_visible=visible,
        name="Test Company",
        description="desc",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


# =========================
# GET ALL
# =========================

@pytest.mark.asyncio
async def test_get_all_companies(service, repo, user):
    companies = [make_company(user.id)]

    repo.get_all_visible_companies.return_value = companies
    repo.count_visible_companies.return_value = 1

    result = await service.get_all_companies(user, 10, 0)

    assert result.total == 1
    assert len(result.companies) == 1
    repo.get_all_visible_companies.assert_called_once()


# =========================
# GET BY ID
# =========================

@pytest.mark.asyncio
async def test_get_company_success(service, repo, user):
    company = make_company(user.id)

    repo.get_company_by_id.return_value = company

    result = await service.get_company_by_id(company.id, user)

    assert result.id == company.id


@pytest.mark.asyncio
async def test_get_company_not_found(service, repo, user):
    repo.get_company_by_id.return_value = None

    with pytest.raises(CompanyNotFound):
        await service.get_company_by_id(uuid4(), user)


@pytest.mark.asyncio
async def test_get_company_forbidden(service, repo, user):
    company = make_company(owner_id=uuid4(), visible=False)

    repo.get_company_by_id.return_value = company

    with pytest.raises(CompanyForbidden):
        await service.get_company_by_id(company.id, user)


# =========================
# CREATE
# =========================

@pytest.mark.asyncio
async def test_create_company(service, repo, user):
    company = make_company(user.id)

    repo.create_company.return_value = company

    data = CompanyCreateRequest(
        name="Test",
        description="desc",
        is_visible=True
    )

    result = await service.create_company(user, data)

    assert result.id == company.id
    repo.create_company.assert_called_once()


# =========================
# UPDATE
# =========================

@pytest.mark.asyncio
async def test_update_not_found(service, repo, user):
    repo.get_company_by_id.return_value = None

    with pytest.raises(CompanyNotFound):
        await service.update_company(uuid4(), user, CompanyUpdateRequest(name="x"))


@pytest.mark.asyncio
async def test_update_forbidden_owner(service, repo, user):
    company = make_company(owner_id=uuid4())

    repo.get_company_by_id.return_value = company

    with pytest.raises(CompanyNotFound):
        await service.update_company(company.id, user, CompanyUpdateRequest(name="x"))


@pytest.mark.asyncio
async def test_update_empty_payload(service, repo, user):
    company = make_company(user.id)

    repo.get_company_by_id.return_value = company

    with pytest.raises(CompanyForbidden):
        await service.update_company(company.id, user, CompanyUpdateRequest())


@pytest.mark.asyncio
async def test_update_success(service, repo, user):
    company = make_company(user.id)
    updated = make_company(user.id)

    repo.get_company_by_id.return_value = company
    repo.update_company.return_value = updated

    data = CompanyUpdateRequest(name="new name")

    result = await service.update_company(company.id, user, data)

    assert result.id == updated.id
    repo.update_company.assert_called_once()


# =========================
# DELETE
# =========================

@pytest.mark.asyncio
async def test_delete_not_found(service, repo, user):
    repo.get_company_by_id.return_value = None

    with pytest.raises(CompanyNotFound):
        await service.delete_company(uuid4(), user)


@pytest.mark.asyncio
async def test_delete_forbidden(service, repo, user):
    company = make_company(owner_id=uuid4())

    repo.get_company_by_id.return_value = company

    with pytest.raises(CompanyNotFound):
        await service.delete_company(company.id, user)


@pytest.mark.asyncio
async def test_delete_success(service, repo, user):
    company = make_company(user.id)

    repo.get_company_by_id.return_value = company

    await service.delete_company(company.id, user)

    repo.delete_company.assert_called_once()
