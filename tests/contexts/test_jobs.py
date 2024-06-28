from ajb.contexts.companies.jobs.usecase import JobsUseCase
from ajb.contexts.companies.jobs.repository import JobRepository
from ajb.contexts.companies.jobs.models import UserCreateJob
from ajb.base.models import QueryFilterParams

from ajb.fixtures.companies import CompanyFixture
from ajb.fixtures.applications import ApplicationFixture
from ajb.fixtures.subscriptions import SubscriptionFixture


def test_create_job(request_scope, mock_openai):
    company = CompanyFixture(request_scope).create_company()
    job_to_create = UserCreateJob(position_title="test")

    # Setup company subscription
    SubscriptionFixture().setup_company_subscription(
        request_scope=request_scope, company_id=company.id
    )

    # Create job
    created_job = JobsUseCase(request_scope, mock_openai).create_job(
        company.id, job_to_create
    )
    assert created_job.position_title == "test"


def test_create_many_jobs(request_scope, mock_openai):
    company = CompanyFixture(request_scope).create_company()
    created_jobs = JobsUseCase(request_scope, mock_openai).create_many_jobs(
        company.id,
        jobs=[
            UserCreateJob(position_title="test"),
            UserCreateJob(position_title="test"),
            UserCreateJob(position_title="test"),
        ],
    )

    assert len(created_jobs) == 3


def test_query_company_jobs(request_scope):
    company_fixture = CompanyFixture(request_scope)
    company = company_fixture.create_company()
    this_job = company_fixture.create_company_job(company.id)
    company_fixture.create_company_job(company.id)
    company_fixture.create_company_job(company.id)
    app_job = company_fixture.create_company_job(company.id)

    application_fixture = ApplicationFixture(request_scope)
    application_fixture.create_application(app_job.company_id, app_job.id, "resume")
    application_fixture.create_application(app_job.company_id, app_job.id, "resume")

    query = QueryFilterParams(page=0, page_size=2)
    response, count = JobRepository(request_scope, company.id).get_company_jobs(
        company.id, None, query
    )

    assert count == 4
    assert len(response) == 2

    # Now make 1 inactive
    JobRepository(request_scope, company.id).update_fields(this_job.id, active=False)
    response, count = JobRepository(request_scope, company.id).get_company_jobs(
        company.id, True
    )

    assert count == 3
    assert len(response) == 3

    response, count = JobRepository(request_scope, company.id).get_company_jobs(
        company.id, False
    )

    assert count == 1
    assert len(response) == 1
