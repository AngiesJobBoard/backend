from datetime import datetime
from unittest.mock import patch
from aiohttp import ClientSession
import pytest

from ajb.base.models import RepoFilterParams
from ajb.contexts.applications.repository import CompanyApplicationRepository
from ajb.contexts.applications.usecase import ApplicationUseCase
from ajb.contexts.applications.models import (
    Application,
    Qualifications,
    Location,
    WorkHistory,
    Education,
    CreateApplication,
    CreateApplicationStatusUpdate,
    ScanStatus,
)
from ajb.contexts.companies.repository import CompanyRepository
from ajb.contexts.companies.jobs.repository import JobRepository
from ajb.contexts.applications.matching.usecase import ApplicantMatchUsecase
from ajb.contexts.applications.matching.ai_matching import ApplicantMatchScore
from ajb.contexts.applications.recruiter_updates.repository import (
    RecruiterUpdatesRepository,
)
from ajb.contexts.applications.repository import ApplicationRepository
from ajb.contexts.companies.notifications.repository import (
    CompanyNotificationRepository,
)
from ajb.vendor.arango.models import Filter, Operator
from ajb.vendor.openai.repository import AsyncOpenAIRepository
from ajb.fixtures.companies import CompanyFixture
from ajb.fixtures.applications import ApplicationFixture


def test_company_view_list_basic(request_scope):
    app_data = ApplicationFixture(request_scope).create_all_application_data()
    repo = CompanyApplicationRepository(request_scope)

    res, count = repo.get_company_view_list(app_data.company.id)
    assert len(res) == 1
    assert count == 1

    res, count = repo.get_company_view_list(app_data.company.id, job_id=app_data.job.id)
    assert len(res) == 1
    assert count == 1


def test_match_score_minimum(request_scope):
    app_data = ApplicationFixture(request_scope).create_all_application_data()
    repo = CompanyApplicationRepository(request_scope)

    # No match score on this record
    res, count = repo.get_company_view_list(app_data.company.id, match_score=50)
    assert len(res) == 0
    assert count == 0

    # Match updated to a low score
    repo.update_fields(app_data.application.id, application_match_score=25)

    res, count = repo.get_company_view_list(app_data.company.id, match_score=50)
    assert len(res) == 0
    assert count == 0

    # Match score higher now
    repo.update_fields(app_data.application.id, application_match_score=75)

    res, count = repo.get_company_view_list(app_data.company.id, match_score=50)
    assert len(res) == 1
    assert count == 1


def test_search_applicants_by_resume_text(request_scope):
    app_data = ApplicationFixture(request_scope).create_all_application_data()
    repo = CompanyApplicationRepository(request_scope)

    # Update with some fake resume text
    repo.update_fields(
        app_data.application.id,
        extracted_resume_text="I am a software engineer with experience in python",
    )

    # Search for Python
    res, count = repo.get_company_view_list(
        app_data.company.id, resume_text_contains="python"
    )
    assert len(res) == 1
    assert count == 1


def test_search_applications_by_skills(request_scope):
    app_data = ApplicationFixture(request_scope).create_all_application_data()
    repo = CompanyApplicationRepository(request_scope)

    # Default job fixture comes with [Python, Another Fancy Skill]
    res, _ = repo.get_company_view_list(app_data.company.id, has_required_skill="Py")
    assert len(res) == 1

    res, _ = repo.get_company_view_list(
        app_data.company.id, has_required_skill="nolo existo"
    )
    assert len(res) == 0


def test_get_many_applications(request_scope):
    fixture = ApplicationFixture(request_scope)
    app_data_1 = fixture.create_all_application_data()
    app_data_2 = fixture.create_application(
        app_data_1.company.id, app_data_1.job.id, app_data_1.resume.id
    )

    query = RepoFilterParams(
        filters=[
            Filter(
                field="_key",
                operator=Operator.ARRAY_IN,
                value=[app_data_1.application.id, app_data_2.id],
            )
        ],
    )
    results = CompanyApplicationRepository(request_scope).get_company_view_list(
        app_data_1.company.id, query
    )
    assert len(results) == 2


def test_extract_application_filter_information():
    application = Application(
        id="abc",
        created_at=datetime.now(),
        created_by="test",
        updated_at=datetime.now(),
        updated_by="test",
        company_id="test",
        job_id="test",
        name="test",
        email="test@test.com",
        qualifications=Qualifications(
            most_recent_job=WorkHistory(
                job_title="Software Engineer",
                start_date=datetime(2020, 1, 1),
                end_date=datetime(2021, 1, 1),
            ),
            work_history=[
                WorkHistory(
                    job_title="Software Engineer",
                    start_date=datetime(2020, 1, 1),
                    end_date=datetime(2021, 1, 1),
                ),
                WorkHistory(
                    job_title="Software Intern",
                    start_date=datetime(2019, 1, 1),
                    end_date=datetime(2019, 6, 1),
                ),
            ],
            education=[
                Education(level_of_education="high school"),
                Education(level_of_education="college"),
            ],
        ),
        user_location=Location(lat=1, lng=1),
    )

    application.extract_filter_information()

    assert application.additional_filters
    assert application.additional_filters.average_job_duration_in_months == 8
    assert application.additional_filters.average_job_duration_in_months == 8
    assert application.additional_filters.total_years_in_workforce == 1
    assert application.additional_filters.years_since_first_job == 1
    assert application.additional_filters.has_college_degree is True


def test_extract_application_distance_and_same_state():
    application = Application(
        id="abc",
        created_at=datetime.now(),
        created_by="test",
        updated_at=datetime.now(),
        updated_by="test",
        company_id="test",
        job_id="test",
        name="test",
        email="test@test.com",
        user_location=Location(lat=1, lng=1),
    )

    miles_between_job_and_applicant = application.get_miles_from_job_location(0, 0)
    with patch(
        "ajb.contexts.applications.models.get_state_from_lat_long"
    ) as mock_get_state:
        mock_get_state.return_value = "nice"
        applicant_in_same_state = application.applicant_is_in_same_state_as_job(0, 0)

    assert miles_between_job_and_applicant == 157
    assert applicant_in_same_state is True


# pylint: disable=too-many-statements
def test_application_counts(request_scope):
    company_fixture = CompanyFixture(request_scope)
    company = company_fixture.create_company()
    job = company_fixture.create_company_job(company.id)

    company_repo = CompanyRepository(request_scope)
    job_repo = JobRepository(request_scope, company.id)

    # Company and job should counts of 0
    retrieved_company = company_repo.get(company.id)
    retrieved_job = job_repo.get(job.id)

    assert retrieved_company.total_applicants == 0
    assert retrieved_company.high_matching_applicants == 0
    assert retrieved_company.new_applicants == 0

    assert retrieved_job.total_applicants == 0
    assert retrieved_job.high_matching_applicants == 0
    assert retrieved_job.new_applicants == 0

    usecase = ApplicationUseCase(request_scope)
    usecase.create_application(
        company.id,
        job.id,
        CreateApplication(
            company_id=company.id,
            job_id=job.id,
            name="apply guy",
            email="apply@guy.com",
        ),
        False,
    )

    retrieved_company = company_repo.get(company.id)
    retrieved_job = job_repo.get(job.id)

    assert retrieved_company.total_applicants == 1
    assert retrieved_company.high_matching_applicants == 0
    assert retrieved_company.new_applicants == 1

    assert retrieved_job.total_applicants == 1
    assert retrieved_job.high_matching_applicants == 0
    assert retrieved_job.new_applicants == 1

    retrieved_company = company_repo.get(company.id)
    retrieved_job = job_repo.get(job.id)

    assert retrieved_company.total_applicants == 1
    assert retrieved_company.high_matching_applicants == 0
    assert retrieved_company.new_applicants == 1

    assert retrieved_job.total_applicants == 1
    assert retrieved_job.high_matching_applicants == 0
    assert retrieved_job.new_applicants == 1

    usecase.delete_all_applications_for_job(company.id, job.id)

    retrieved_company = company_repo.get(company.id)
    retrieved_job = job_repo.get(job.id)

    assert retrieved_company.total_applicants == 0
    assert retrieved_company.high_matching_applicants == 0
    assert retrieved_company.new_applicants == 0

    assert retrieved_job.total_applicants == 0
    assert retrieved_job.high_matching_applicants == 0
    assert retrieved_job.new_applicants == 0


@pytest.mark.asyncio
async def test_high_matching_applicants(request_scope):
    company_fixture = CompanyFixture(request_scope)
    company = company_fixture.create_company()
    job = company_fixture.create_company_job(company.id)
    usecase = ApplicationUseCase(request_scope)
    created_application = usecase.create_application(
        company.id,
        job.id,
        CreateApplication(
            company_id=company.id,
            job_id=job.id,
            name="apply guy",
            email="apply@guy.com",
        ),
        False,
    )

    company_repo = CompanyRepository(request_scope)
    job_repo = JobRepository(request_scope, company.id)

    async with ClientSession() as session:
        matcher_usecase = ApplicantMatchUsecase(
            request_scope, AsyncOpenAIRepository(session)
        )

        with patch(
            "ajb.contexts.applications.matching.usecase.ApplicantMatchUsecase.get_match"
        ) as mock_get_match:
            mock_get_match.return_value = ApplicantMatchScore(
                match_score=100, match_reason="test"
            )
            await matcher_usecase.update_application_with_match_score(
                created_application.id, job
            )

    retrieved_company = company_repo.get(company.id)
    retrieved_job = job_repo.get(job.id)

    assert retrieved_company.total_applicants == 1
    assert retrieved_company.high_matching_applicants == 1
    assert retrieved_company.new_applicants == 1

    assert retrieved_job.total_applicants == 1
    assert retrieved_job.high_matching_applicants == 1
    assert retrieved_job.new_applicants == 1

    usecase.delete_all_applications_for_job(company.id, job.id)

    retrieved_company = company_repo.get(company.id)
    retrieved_job = job_repo.get(job.id)

    assert retrieved_company.total_applicants == 0
    assert retrieved_company.high_matching_applicants == 0
    assert retrieved_company.new_applicants == 0

    assert retrieved_job.total_applicants == 0
    assert retrieved_job.high_matching_applicants == 0
    assert retrieved_job.new_applicants == 0


def test_application_status_update(request_scope):
    app_data = ApplicationFixture(request_scope).create_all_application_data()
    usecase = ApplicationUseCase(request_scope)
    recruiter_update_repo = RecruiterUpdatesRepository(request_scope)
    company_notifications_repo = CompanyNotificationRepository(request_scope)

    request_scope.user_id = app_data.admin.id
    assert len(recruiter_update_repo.get_all()) == 0
    assert len(company_notifications_repo.get_all()) == 0

    updated_application = usecase.recruiter_updates_application_status(
        app_data.company.id,
        app_data.job.id,
        app_data.application.id,
        CreateApplicationStatusUpdate(
            application_status="Hired", update_reason="This is a test"
        ),
    )

    # Check status updated occurred
    assert updated_application.application_status == "Hired"

    assert len(recruiter_update_repo.get_all()) == 1


def test_get_pending_applications(request_scope):
    app_data = ApplicationFixture(request_scope).create_all_application_data()
    another_job = CompanyFixture(request_scope).create_company_job(app_data.company.id)
    app_repo = ApplicationRepository(request_scope)
    company_app_repo = CompanyApplicationRepository(request_scope)

    # Make 1 application that matches each of the expected statuses
    scan_pending = app_data.application.model_copy()
    scan_started = app_data.application.model_copy()
    scan_failed = app_data.application.model_copy()
    matching_score_pending = app_data.application.model_copy()
    matching_score_started = app_data.application.model_copy()

    scan_completed_match_pending = app_data.application.model_copy()
    scan_completed_match_started = app_data.application.model_copy()
    scan_completed_match_completed = app_data.application.model_copy()

    scan_pending.resume_scan_status = ScanStatus.PENDING
    scan_started.resume_scan_status = ScanStatus.STARTED
    scan_failed.resume_scan_status = ScanStatus.FAILED
    matching_score_pending.match_score_status = ScanStatus.PENDING
    matching_score_started.match_score_status = ScanStatus.STARTED

    scan_completed_match_pending.resume_scan_status = ScanStatus.COMPLETED
    scan_completed_match_pending.match_score_status = ScanStatus.PENDING
    scan_completed_match_started.resume_scan_status = ScanStatus.COMPLETED
    scan_completed_match_started.match_score_status = ScanStatus.STARTED
    scan_completed_match_completed.resume_scan_status = ScanStatus.COMPLETED
    scan_completed_match_completed.match_score_status = ScanStatus.COMPLETED

    scan_started.job_id = another_job.id
    scan_failed.job_id = another_job.id

    for app in [
        scan_pending,
        scan_started,
        scan_failed,
        matching_score_pending,
        matching_score_started,
        scan_completed_match_pending,
        scan_completed_match_started,
        scan_completed_match_completed,
    ]:
        app = app_repo.create(CreateApplication(**app.model_dump()))

    # Not include failed
    pending_results, count = company_app_repo.get_all_pending_applications(
        app_data.company.id
    )
    assert len(pending_results) == 6
    assert count == 6

    # Include failed
    pending_results, count = company_app_repo.get_all_pending_applications(
        app_data.company.id, include_failed=True
    )
    assert len(pending_results) == 7
    assert count == 7

    # Query on specific job no failed
    pending_results, count = company_app_repo.get_all_pending_applications(
        app_data.company.id, job_id=another_job.id
    )
    assert len(pending_results) == 1
    assert count == 1

    # Query on specific job and include failed
    pending_results, count = company_app_repo.get_all_pending_applications(
        app_data.company.id, job_id=another_job.id, include_failed=True
    )
    assert len(pending_results) == 2
    assert count == 2
