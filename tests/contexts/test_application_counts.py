from ajb.base.models import RepoFilterParams
from ajb.contexts.applications.models import CreateApplication
from ajb.contexts.applications.repository import CompanyApplicationRepository
from ajb.contexts.companies.jobs.repository import JobRepository
from ajb.contexts.companies.repository import CompanyRepository
from ajb.fixtures.companies import CompanyFixture
from ajb.contexts.applications.usecase import ApplicationUseCase
from ajb.vendor.arango.models import Filter, Operator
from api.app.contexts.companies.jobs import mark_job_as_active, mark_job_as_inactive


class MockRequest:  # Class for mocking Starlette requests
    def __init__(self, request_scope):
        self.state = type("state", (), {})()
        self.state.request_scope = request_scope


def check_total_company_application_counts(
    request_scope, company_id, expected_total, expected_new, expected_high_match
):
    """Helper method for validating number of applicants to an entire company"""
    repo = CompanyApplicationRepository(request_scope)
    total_count = repo.get_count(company_id=company_id)
    new_count = repo.get_count(
        repo_filters=RepoFilterParams(
            filters=[
                Filter(
                    field="application_status", operator=Operator.IS_NULL, value=None
                ),
                Filter(field="company_id", value=company_id),
            ]
        )
    )
    high_match_count = repo.get_count(
        repo_filters=RepoFilterParams(
            filters=[
                Filter(
                    field="application_match_score",
                    operator=Operator.GREATER_THAN_EQUAL,
                    value=70,
                ),
                Filter(field="company_id", value=company_id),
            ]
        )
    )
    assert total_count == expected_total
    assert new_count == expected_new
    assert high_match_count == expected_high_match


def check_active_company_application_counts(
    request_scope, company_id, expected_total, expected_new, expected_high_match
):
    """Helper method for validating number of active applicants to an entire company"""
    company_repo = CompanyRepository(request_scope)

    company = company_repo.get(company_id)

    assert company.total_applicants == expected_total
    assert company.new_applicants == expected_new
    assert company.high_matching_applicants == expected_high_match


def check_job_application_counts(
    request_scope, job_id, expected_total, expected_new, expected_high_match
):
    """Helper method for validating number of applicants for a specific job"""
    repo = CompanyApplicationRepository(request_scope)
    total_count = repo.get_count(job_id=job_id)
    new_count = repo.get_count(
        repo_filters=RepoFilterParams(
            filters=[
                Filter(
                    field="application_status", operator=Operator.IS_NULL, value=None
                ),
                Filter(field="job_id", value=job_id),
            ]
        )
    )
    high_match_count = repo.get_count(
        repo_filters=RepoFilterParams(
            filters=[
                Filter(
                    field="application_match_score",
                    operator=Operator.GREATER_THAN_EQUAL,
                    value=70,
                ),
                Filter(field="job_id", value=job_id),
            ]
        )
    )
    assert total_count == expected_total
    assert new_count == expected_new
    assert high_match_count == expected_high_match


def test_mark_job_active(request_scope):
    company_fixture = CompanyFixture(request_scope)
    company = company_fixture.create_company()
    job1 = company_fixture.create_company_job(company.id)
    job2 = company_fixture.create_company_job(company.id)

    request = MockRequest(request_scope)

    usecase = ApplicationUseCase(request_scope)
    applications = [
        CreateApplication(
            company_id=company.id,
            job_id=job1.id,
            name="john doe",
            email="johndoe@applicant.com",
        ),
        CreateApplication(
            company_id=company.id,
            job_id=job1.id,
            name="jane doe",
            email="janedoe@applicant.com",
        ),
    ]

    # Create applications for job 1
    usecase.create_many_applications(
        company_id=company.id,
        job_id=job1.id,
        partial_applications=applications,
        produce_submission_event=False,
    )

    # Create application for job 2
    created_application = usecase.create_application(
        company.id,
        job2.id,
        CreateApplication(
            company_id=company.id,
            job_id=job2.id,
            name="apply guy",
            email="apply@guy.com",
        ),
        False,
    )

    # Sanity checks to ensure successful creation
    check_job_application_counts(request_scope, job1.id, 2, 2, 0)
    check_job_application_counts(request_scope, job2.id, 1, 1, 0)
    check_total_company_application_counts(request_scope, company.id, 3, 3, 0)
    check_active_company_application_counts(request_scope, company.id, 3, 3, 0)

    # Test mark job as inactive
    mark_job_as_inactive(request, company.id, job1.id)  # Make job 1 inactive
    check_active_company_application_counts(
        request_scope, company.id, 1, 1, 0
    )  # Job 1's applicants should now be inactive, leaving only the job 2 applicant.

    # Test mark job as active
    mark_job_as_active(request, company.id, job1.id)  # Make job active again
    check_active_company_application_counts(
        request_scope, company.id, 3, 3, 0
    )  # Job 1 applicants should come back now


# AJBTODO: these are some more endpoints we can try and hit
# upload_applications_from_resume
# upload_application_from_text_dump
# rerun_match_score
# update_resume_scan_text
# update_application_status
# applicants_api_webhook_handler
