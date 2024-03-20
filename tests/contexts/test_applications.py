from datetime import datetime
from unittest.mock import patch
from aiohttp import ClientSession
import pytest

from ajb.fixtures.applications import ApplicationFixture
from ajb.contexts.applications.repository import CompanyApplicationRepository
from ajb.contexts.applications.usecase import ApplicationUseCase
from ajb.contexts.applications.models import (
    Application,
    Qualifications,
    Location,
    WorkHistory,
    Education,
    CreateApplication,
)
from ajb.contexts.companies.repository import CompanyRepository
from ajb.contexts.companies.jobs.repository import JobRepository
from ajb.contexts.applications.matching.usecase import ApplicantMatchUsecase
from ajb.contexts.applications.matching.ai_matching import ApplicantMatchScore
from ajb.fixtures.companies import CompanyFixture
from ajb.vendor.arango.models import Filter, Operator
from ajb.vendor.openai.repository import AsyncOpenAIRepository
from ajb.base.models import RepoFilterParams


def test_company_view_list_basic(request_scope):
    app_data = ApplicationFixture(request_scope).create_all_application_data()
    repo = CompanyApplicationRepository(request_scope)

    res, count = repo.get_company_view_list(app_data.company.id)
    assert len(res) == 1
    assert count == 1

    res, count = repo.get_company_view_list(app_data.company.id, job_id=app_data.job.id)
    assert len(res) == 1
    assert count == 1


def test_company_view_shortlist(request_scope):
    app_data = ApplicationFixture(request_scope).create_all_application_data()
    repo = CompanyApplicationRepository(request_scope)

    res, count = repo.get_company_view_list(app_data.company.id, shortlist_only=True)
    assert len(res) == 0
    assert count == 0

    repo.update_fields(app_data.application.id, appplication_is_shortlisted=True)

    res, count = repo.get_company_view_list(app_data.company.id, shortlist_only=True)
    assert len(res) == 1
    assert count == 1


def test_company_view_new_only(request_scope):
    app_data = ApplicationFixture(request_scope).create_all_application_data()
    repo = CompanyApplicationRepository(request_scope)

    res, count = repo.get_company_view_list(app_data.company.id, new_only=True)
    assert len(res) == 1
    assert count == 1

    repo.update_fields(app_data.application.id, viewed_by_company=True)

    res, count = repo.get_company_view_list(app_data.company.id, new_only=True)
    assert len(res) == 0
    assert count == 0


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


def test_application_counts(request_scope):
    company_fixture = CompanyFixture(request_scope)
    company = company_fixture.create_company()
    request_scope.company_id = company.id
    job = company_fixture.create_company_job(company.id)

    company_repo = CompanyRepository(request_scope)
    job_repo = JobRepository(request_scope, company.id)

    # Company and job should counts of 0
    retrieved_company = company_repo.get(company.id)
    retrieved_job = job_repo.get(job.id)

    assert retrieved_company.total_applicants == 0
    assert retrieved_company.shortlisted_applicants == 0
    assert retrieved_company.high_matching_applicants == 0
    assert retrieved_company.new_applicants == 0

    assert retrieved_job.total_applicants == 0
    assert retrieved_job.shortlisted_applicants == 0
    assert retrieved_job.high_matching_applicants == 0
    assert retrieved_job.new_applicants == 0

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

    retrieved_company = company_repo.get(company.id)
    retrieved_job = job_repo.get(job.id)

    assert retrieved_company.total_applicants == 1
    assert retrieved_company.shortlisted_applicants == 0
    assert retrieved_company.high_matching_applicants == 0
    assert retrieved_company.new_applicants == 1

    assert retrieved_job.total_applicants == 1
    assert retrieved_job.shortlisted_applicants == 0
    assert retrieved_job.high_matching_applicants == 0
    assert retrieved_job.new_applicants == 1

    usecase.company_updates_application_shortlist(
        company.id, created_application.id, True
    )

    retrieved_company = company_repo.get(company.id)
    retrieved_job = job_repo.get(job.id)

    assert retrieved_company.total_applicants == 1
    assert retrieved_company.shortlisted_applicants == 1
    assert retrieved_company.high_matching_applicants == 0
    assert retrieved_company.new_applicants == 1

    assert retrieved_job.total_applicants == 1
    assert retrieved_job.shortlisted_applicants == 1
    assert retrieved_job.high_matching_applicants == 0
    assert retrieved_job.new_applicants == 1

    usecase.company_views_applications(company.id, [created_application.id])

    retrieved_company = company_repo.get(company.id)
    retrieved_job = job_repo.get(job.id)

    assert retrieved_company.total_applicants == 1
    assert retrieved_company.shortlisted_applicants == 1
    assert retrieved_company.high_matching_applicants == 0
    assert retrieved_company.new_applicants == 0

    assert retrieved_job.total_applicants == 1
    assert retrieved_job.shortlisted_applicants == 1
    assert retrieved_job.high_matching_applicants == 0
    assert retrieved_job.new_applicants == 0

    usecase.delete_all_applications_for_job(company.id, job.id)

    retrieved_company = company_repo.get(company.id)
    retrieved_job = job_repo.get(job.id)

    assert retrieved_company.total_applicants == 0
    assert retrieved_company.shortlisted_applicants == 0
    assert retrieved_company.high_matching_applicants == 0
    assert retrieved_company.new_applicants == 0

    assert retrieved_job.total_applicants == 0
    assert retrieved_job.shortlisted_applicants == 0
    assert retrieved_job.high_matching_applicants == 0
    assert retrieved_job.new_applicants == 0


@pytest.mark.asyncio
async def test_high_matching_applicants(request_scope):
    company_fixture = CompanyFixture(request_scope)
    company = company_fixture.create_company()
    request_scope.company_id = company.id
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
    assert retrieved_company.shortlisted_applicants == 0
    assert retrieved_company.high_matching_applicants == 1
    assert retrieved_company.new_applicants == 1

    assert retrieved_job.total_applicants == 1
    assert retrieved_job.shortlisted_applicants == 0
    assert retrieved_job.high_matching_applicants == 1
    assert retrieved_job.new_applicants == 1

    usecase.delete_all_applications_for_job(company.id, job.id)

    retrieved_company = company_repo.get(company.id)
    retrieved_job = job_repo.get(job.id)

    assert retrieved_company.total_applicants == 0
    assert retrieved_company.shortlisted_applicants == 0
    assert retrieved_company.high_matching_applicants == 0
    assert retrieved_company.new_applicants == 0

    assert retrieved_job.total_applicants == 0
    assert retrieved_job.shortlisted_applicants == 0
    assert retrieved_job.high_matching_applicants == 0
    assert retrieved_job.new_applicants == 0
