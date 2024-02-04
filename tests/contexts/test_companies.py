import pytest

from ajb.contexts.companies.usecase import CompaniesUseCase, UserCreateCompany
from ajb.contexts.companies.repository import CompanyRepository
from ajb.contexts.companies.recruiters.repository import RecruiterRepository
from ajb.contexts.companies.recruiters.models import RecruiterRole
from ajb.exceptions import CompanyCreateException

from ajb.fixtures.users import UserFixture


def test_create_company_usecase(request_scope):
    user = UserFixture(request_scope).create_user()

    # First create the company with the usecase
    use_case = CompaniesUseCase(request_scope)
    created_company = use_case.user_create_company(
        data=UserCreateCompany(name="testy"), creating_user_id=user.id
    )

    # Now expect to see the company created and the user tagged as the owner connected by the recruiter edge
    company_repo = CompanyRepository(request_scope)
    recruiter_repo = RecruiterRepository(request_scope, created_company.id)

    assert company_repo.get(created_company.id)
    recruiters, _ = recruiter_repo.query(user_id=user.id)
    assert recruiters[0].role == RecruiterRole.OWNER

    # Now check it matches with the use case function
    user_companies = use_case.get_companies_by_user(user.id)
    assert len(user_companies) == 1
    assert user_companies[0].id == created_company.id


def test_company_with_existing_slug(request_scope):
    user = UserFixture(request_scope).create_user()
    use_case = CompaniesUseCase(request_scope)
    use_case.user_create_company(
        data=UserCreateCompany(name="testy", slug="test"), creating_user_id=user.id
    )

    with pytest.raises(CompanyCreateException):
        use_case.user_create_company(
            data=UserCreateCompany(name="testy", slug="test"), creating_user_id=user.id
        )
