from datetime import datetime

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.message import Message

from unittest.mock import patch
import pytest

from ajb.base.models import RepoFilterParams
from ajb.config.settings import SETTINGS

from ajb.contexts.applications.extract_data.ai_extractor import ExtractedResume
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
from ajb.contexts.companies.email_ingress_webhooks.models import (
    CompanyEmailIngress,
    EmailIngressType,
)
from ajb.contexts.companies.repository import CompanyRepository
from ajb.contexts.companies.jobs.repository import JobRepository
from ajb.contexts.companies.jobs.usecase import JobsUseCase
from ajb.contexts.applications.matching.usecase import ApplicantMatchUsecase
from ajb.contexts.applications.matching.ai_matching import ApplicantMatchScore
from ajb.contexts.applications.recruiter_updates.repository import (
    RecruiterUpdatesRepository,
)
from ajb.contexts.applications.repository import ApplicationRepository
from ajb.contexts.companies.notifications.repository import (
    CompanyNotificationRepository,
)
from ajb.contexts.resumes.models import UserCreateResume
from ajb.fixtures.subscriptions import SubscriptionFixture
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
    assert application.additional_filters.average_gap_duration_in_months == 7
    assert application.additional_filters.total_years_in_workforce == 1
    assert application.additional_filters.years_since_first_job == 1


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

    # Setup company subscription
    SubscriptionFixture().setup_company_subscription(
        request_scope=request_scope, company_id=company.id
    )

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
        True,
    )

    # Validate a kafka request was created
    assert len(request_scope.kafka.messages[SETTINGS.KAFKA_APPLICATIONS_TOPIC]) == 1

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


@pytest.mark.asyncio
async def test_high_matching_applicants(request_scope):
    company_fixture = CompanyFixture(request_scope)
    company = company_fixture.create_company()
    job = company_fixture.create_company_job(company.id)
    usecase = ApplicationUseCase(request_scope)

    # Setup company subscription
    SubscriptionFixture().setup_company_subscription(
        request_scope=request_scope, company_id=company.id
    )

    # Create application
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

    matcher_usecase = ApplicantMatchUsecase(request_scope, AsyncOpenAIRepository())

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
    assert len(pending_results) == 4
    assert count == 4

    # Include failed
    pending_results, count = company_app_repo.get_all_pending_applications(
        app_data.company.id, include_failed=True
    )
    assert len(pending_results) == 5
    assert count == 5

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


def test_applications_with_job_active_filter(request_scope):
    app_data = ApplicationFixture(request_scope).create_all_application_data()
    app_repo = ApplicationRepository(request_scope)
    job_repo = JobRepository(request_scope, app_data.company.id)
    company_app_repo = CompanyApplicationRepository(request_scope)

    # Should get 1 application from query
    results, count = company_app_repo.get_company_view_list(
        company_id=app_data.company.id
    )

    assert len(results) == 1
    assert count == 1

    # Update job to not be active
    job_repo.update_fields(app_data.job.id, active=False)

    # Still expect to get 1 because there is no status filter
    results, count = company_app_repo.get_company_view_list(
        company_id=app_data.company.id
    )

    assert len(results) == 1
    assert count == 1

    # Now update app and query with a status filter
    app_repo.update_fields(app_data.application.id, application_status="In Review")
    results, count = company_app_repo.get_company_view_list(
        company_id=app_data.company.id, status_filter=["In Review"]
    )

    # Expect to get 0 now
    assert len(results) == 0
    assert count == 0

    # Update back to True
    job_repo.update_fields(app_data.job.id, active=True)

    # Now expect to get 1 application
    results, count = company_app_repo.get_company_view_list(
        company_id=app_data.company.id
    )

    assert len(results) == 1
    assert count == 1


def test_company_counts_with_job_active_filter(request_scope):
    app_data = ApplicationFixture(request_scope).create_all_application_data()
    company_repo = CompanyRepository(request_scope)
    job_usecase = JobsUseCase(request_scope)

    # The fixture doesn't actually update the company counts... so set the company counts to 1
    company_repo.update_fields(app_data.company.id, total_applicants=1, total_jobs=1)

    # Expect job and application counts to be 1
    company = company_repo.get(app_data.company.id)
    assert company.total_applicants == 1
    assert company.total_jobs == 1

    # Now make the job inactive
    job_usecase.update_job_active_status(app_data.company.id, app_data.job.id, False)

    # Now the counts should be 0
    company = company_repo.get(app_data.company.id)
    assert company.total_applicants == 0
    assert company.total_jobs == 0

    # Make it active again
    job_usecase.update_job_active_status(app_data.company.id, app_data.job.id, True)

    # Now the counts should be 1
    company = company_repo.get(app_data.company.id)
    assert company.total_applicants == 1
    assert company.total_jobs == 1


def test_create_many_applications(request_scope):
    company_fixture = CompanyFixture(request_scope)
    company = company_fixture.create_company()
    job = company_fixture.create_company_job(company.id)

    company_repo = CompanyRepository(request_scope)
    job_repo = JobRepository(request_scope, company.id)

    # Verify that we are starting with 0 applicants
    retrieved_company = company_repo.get(company.id)
    retrieved_job = job_repo.get(job.id)

    assert retrieved_company.total_applicants == 0
    assert retrieved_company.high_matching_applicants == 0
    assert retrieved_company.new_applicants == 0

    assert retrieved_job.total_applicants == 0
    assert retrieved_job.high_matching_applicants == 0
    assert retrieved_job.new_applicants == 0

    usecase = ApplicationUseCase(request_scope)
    applications = [
        CreateApplication(
            company_id=company.id,
            job_id=job.id,
            name="john doe",
            email="johndoe@applicant.com",
        ),
        CreateApplication(
            company_id=company.id,
            job_id=job.id,
            name="jane doe",
            email="janedoe@applicant.com",
        ),
    ]

    # Create applications with kafka patch
    usecase.create_many_applications(
        company_id=company.id,
        job_id=job.id,
        partial_applications=applications,
        produce_submission_event=True,
    )

    # Validate kafka requests were created
    assert len(request_scope.kafka.messages[SETTINGS.KAFKA_APPLICATIONS_TOPIC]) == 2

    # Verify that the 2 applicants were successfully created
    retrieved_company = company_repo.get(company.id)
    retrieved_job = job_repo.get(job.id)

    assert retrieved_company.total_applicants == 2
    assert retrieved_company.high_matching_applicants == 0
    assert retrieved_company.new_applicants == 2

    assert retrieved_job.total_applicants == 2
    assert retrieved_job.high_matching_applicants == 0
    assert retrieved_job.new_applicants == 2

    retrieved_company = company_repo.get(company.id)
    retrieved_job = job_repo.get(job.id)

    assert retrieved_company.total_applicants == 2
    assert retrieved_company.high_matching_applicants == 0
    assert retrieved_company.new_applicants == 2

    assert retrieved_job.total_applicants == 2
    assert retrieved_job.high_matching_applicants == 0
    assert retrieved_job.new_applicants == 2

    # Test application statistics
    statistics = usecase.get_application_statistics(company.id, job.id)
    assert (
        sum(statistics.match_scores.values()) == 2
    )  # Ensure the two applicants have appeared in match scores
    assert (
        sum(statistics.statuses.values()) == 2
    )  # Check that the two applicants have appeared in statuses


def test_create_application_from_resume(request_scope):
    company_fixture = CompanyFixture(request_scope)
    company = company_fixture.create_company()
    job = company_fixture.create_company_job(company.id)

    company_repo = CompanyRepository(request_scope)
    job_repo = JobRepository(request_scope, company.id)

    usecase = ApplicationUseCase(request_scope)

    # Setup company subscription
    SubscriptionFixture().setup_company_subscription(
        request_scope=request_scope, company_id=company.id
    )

    # Prepare data
    resume = UserCreateResume(
        file_type="pdf",
        file_name="test_resume",
        resume_data=bytes(1),
        company_id=company.id,
        job_id=job.id,
    )
    application = CreateApplication(
        company_id=company.id,
        job_id=job.id,
        name="john doe",
        email="johndoe@applicant.com",
    )

    # Create application
    usecase.create_application_from_resume(resume, application)

    # Check for kafka message
    assert len(request_scope.kafka.messages[SETTINGS.KAFKA_APPLICATIONS_TOPIC]) == 2

    # Verify applicant was created
    retrieved_company = company_repo.get(company.id)
    retrieved_job = job_repo.get(job.id)

    assert retrieved_company.total_applicants == 1
    assert retrieved_company.high_matching_applicants == 0
    assert retrieved_company.new_applicants == 1

    assert retrieved_job.total_applicants == 1
    assert retrieved_job.high_matching_applicants == 0
    assert retrieved_job.new_applicants == 1


def test_email_application_ingress(request_scope):
    company_fixture = CompanyFixture(request_scope)
    company = company_fixture.create_company()
    job = company_fixture.create_company_job(company.id)
    usecase = ApplicationUseCase(request_scope)

    # Setup company subscription
    SubscriptionFixture().setup_company_subscription(
        request_scope=request_scope, company_id=company.id
    )

    # Prepare data
    ingress_email = MIMEMultipart()

    company_email_ingress = CompanyEmailIngress(
        company_id=company.id,
        job_id=job.id,
        subdomain="www",
        id="test_ingress_email",
        created_at=datetime.now(),
        created_by="unittest",
        updated_at=datetime.now(),
        updated_by="unittest",
        ingress_type=EmailIngressType.CREATE_APPLICATION,
    )

    # Ensure that it does not succeed with an empty email
    passed_with_empty_email = True
    try:
        usecase.process_email_application_ingress(Message(), company_email_ingress)
    except ValueError:
        passed_with_empty_email = False

    if passed_with_empty_email:
        raise AssertionError(
            "process_email_application_ingress ran anyway with an empty email"
        )

    # Attach multiple parts to email
    ingress_email.attach(MIMEText("Example email body", "plain"))
    ingress_email.attach(MIMEText("Second email part", "plain"))

    # Process email with multiple parts
    usecase.process_email_application_ingress(ingress_email, company_email_ingress)


def test_create_application_from_raw_text(request_scope):
    company_fixture = CompanyFixture(request_scope)
    company = company_fixture.create_company()
    job = company_fixture.create_company_job(company.id)

    usecase = ApplicationUseCase(request_scope)

    # Setup company subscription
    SubscriptionFixture().setup_company_subscription(
        request_scope=request_scope, company_id=company.id
    )

    # Prepare data
    example_resume = ExtractedResume()

    # Make request with patched resume extractor
    with patch(
        "ajb.contexts.applications.extract_data.ai_extractor.SyncronousAIResumeExtractor.get_candidate_profile_from_resume_text",
        return_value=example_resume,
    ):
        usecase.application_is_created_from_raw_text(company.id, job.id, "test")

    # Check that the application creation event was fired
    assert len(request_scope.kafka.messages[SETTINGS.KAFKA_APPLICATIONS_TOPIC]) == 1
