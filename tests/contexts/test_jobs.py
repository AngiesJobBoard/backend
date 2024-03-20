from ajb.contexts.companies.repository import CompanyRepository
from ajb.contexts.companies.jobs.usecase import JobsUseCase
from ajb.contexts.companies.jobs.models import UserCreateJob

from ajb.fixtures.companies import CompanyFixture


def test_create_job(request_scope):
    company = CompanyFixture(request_scope).create_company()
    request_scope.company_id = company.id
    created_job = JobsUseCase(request_scope).create_job(
        company.id, UserCreateJob(position_title="test")
    )

    assert created_job.position_title == "test"

    # Check company has job count of 1
    company_repo = CompanyRepository(request_scope)
    company = company_repo.get(company.id)
    assert company.total_jobs == 1


def test_create_many_jobs(request_scope):
    company = CompanyFixture(request_scope).create_company()
    request_scope.company_id = company.id
    created_jobs = JobsUseCase(request_scope).create_many_jobs(
        company.id,
        jobs=[
            UserCreateJob(position_title="test"),
            UserCreateJob(position_title="test"),
            UserCreateJob(position_title="test"),
        ],
    )

    assert len(created_jobs) == 3

    # Check company has job count of 1
    company_repo = CompanyRepository(request_scope)
    company = company_repo.get(company.id)
    assert company.total_jobs == 3


def test_delete_job(request_scope):
    company = CompanyFixture(request_scope).create_company()
    request_scope.company_id = company.id
    usecase = JobsUseCase(request_scope)
    created_job = usecase.create_job(company.id, UserCreateJob(position_title="test"))
    usecase.delete_job(company.id, created_job.id)

    # Check company has job count of 0
    company_repo = CompanyRepository(request_scope)
    company = company_repo.get(company.id)
    assert company.total_jobs == 0
