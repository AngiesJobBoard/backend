from ajb.contexts.companies.api_ingress_webhooks.models import (
    CreateCompanyAPIIngress,
    IngressSourceType,
)
from ajb.contexts.companies.api_ingress_webhooks.repository import (
    CompanyAPIIngressRepository,
)
from ajb.contexts.companies.api_ingress_webhooks.usecase import APIIngressUsecase
from ajb.contexts.companies.usecase import CompaniesUseCase, UserCreateCompany
from ajb.contexts.companies.repository import CompanyRepository
from ajb.contexts.companies.recruiters.repository import RecruiterRepository
from ajb.contexts.companies.recruiters.models import RecruiterRole

from ajb.fixtures.companies import CompanyFixture
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
    company_1 = use_case.user_create_company(
        data=UserCreateCompany(name="testy", slug="test"), creating_user_id=user.id
    )

    company_2 = use_case.user_create_company(
        data=UserCreateCompany(name="testy", slug="test"), creating_user_id=user.id
    )

    assert company_1.name == company_2.name
    assert company_1.slug != company_2.slug
    assert company_1.id != company_2.id


def test_api_ingress_webhooks(request_scope):
    company_fixture = CompanyFixture(request_scope)
    company = company_fixture.create_company()
    api_ingress_repo = CompanyAPIIngressRepository(request_scope, company.id)
    job = company_fixture.create_company_job(company.id)

    # Create API Ingress Record
    api_ingress_data = CreateCompanyAPIIngress(
        integration_name="test",
        source_type=IngressSourceType.COMPANY_WEBSITE,
        source="PostCardMania Website",
        company_id=company.id,
        secret_key="123",
        salt="456",
        expected_jwt="n/a",
        allowed_ips=[],
    )
    api_ingress_record = api_ingress_repo.create(data=api_ingress_data)

    # Retrieve record and make assertions
    results, count = APIIngressUsecase(request_scope).get_ingress_records_with_count(
        company.id, job.id
    )

    assert count == 1
    assert results[0].id == api_ingress_record.id
