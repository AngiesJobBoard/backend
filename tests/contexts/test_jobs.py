from datetime import datetime
import pytest

from ajb.base import RequestScope
from ajb.contexts.companies.jobs.models import (
    Job,
    CreateJob,
    UserCreateJob,
    ScheduleType,
    ExperienceLevel,
    JobLocationType,
    Location,
    JobSkill,
    WeeklyScheduleType,
    ShiftType,
    Pay,
    PayType,
    AlgoliaJobRecord,
)
from ajb.contexts.companies.jobs.usecase import JobUseCase
from ajb.contexts.companies.jobs.repository import JobRepository
from ajb.contexts.admin.jobs.repository import (
    AdminJobApprovalRepository,
    DataReducedAdminJobPostApproval,
    AdminJobPostApproval,
)
from ajb.contexts.admin.jobs.models import JobApprovalStatus
from ajb.contexts.admin.jobs.usecase import (
    JobApprovalUseCase,
    AdminCreateApprovalUpdate,
)
from ajb.vendor.algolia.repository import (
    AlgoliaClientFactory,
    AlgoliaIndex,
    AlgoliaSearchRepository,
)
from ajb.exceptions import (
    FailedToPostJobException,
    MissingJobFieldsException,
    FailedToUpdateJobException,
)

from ajb.fixtures.companies import CompanyFixture
from ajb.fixtures.users import UserFixture
from ajb.fixtures.applications import ApplicationFixture


def test_basic_create_job(request_scope):
    company = CompanyFixture(request_scope).create_company()
    repo = JobRepository(request_scope, company.id)
    job = repo.create(
        CreateJob(
            company_id=company.id,
            position_title="Software Engineer",
            description="This is a description",
            industry_category="Software Engineering",
            industry_subcategories=["python"],
            schedule=ScheduleType.FULL_TIME,
            experience_required=ExperienceLevel.eleven_or_more_years,
            location_type=JobLocationType.REMOTE,
            location_override=Location(
                address_line_1="100 state st",
                city="Boston",
                state="MA",
                country="USA",
                zipcode="02109",
                lat=42.35843,
                lng=-71.05977,
            ),
            required_job_skills=[JobSkill(skill_name="Python", must_have=True)],
            on_job_training_offered=True,
            weekly_day_range=[WeeklyScheduleType.monday_to_friday],
            shift_type=[ShiftType.day],
            pay=Pay(
                pay_type=PayType.YEARLY,
                pay_min=100000,
                pay_max=200000,
            ),
            language_requirements=["English"],
            background_check_required=True,
            drug_test_required=True,
            felons_accepted=False,
            disability_accepted=True,
        )
    )
    assert job.id is not None
    assert job.position_title == "Software Engineer"


def test_job_submission(request_scope: RequestScope):
    company_fixture = CompanyFixture(request_scope)
    user, company = company_fixture.create_company_with_owner()
    admin_user = UserFixture(request_scope).create_admin_user()
    request_scope.user_id = user.id

    mock_algolia_client = AlgoliaClientFactory._return_mock()
    mock_algolia = AlgoliaSearchRepository(AlgoliaIndex.JOBS, mock_algolia_client)

    job = company_fixture.create_company_job(company.id)
    job_usecase = JobUseCase(request_scope, aloglia_jobs=mock_algolia)
    assert job_usecase.submit_job_for_approval(company.id, job.id)

    # Now check admin job repo and expect to see job
    approval_repo = AdminJobApprovalRepository(request_scope)
    submission = approval_repo.get_one(company_id=company.id, job_id=job.id)
    assert submission is not None
    assert submission.current_approval_status == JobApprovalStatus.PENDING

    # Admin approves job
    approval_usecase = JobApprovalUseCase(request_scope, aloglia_jobs=mock_algolia)
    approval_usecase.update_job_approval_status(
        submission.id,
        user_id=admin_user.id,
        is_admin_update=True,
        updates=AdminCreateApprovalUpdate(
            approval_status=JobApprovalStatus.APPROVED, reason="Looks good bro"
        ),
    )

    # Job is available in search engine
    assert mock_algolia.get(job.id) is not None

    # Job is unposted
    unposted_job = job_usecase.unpost_job(company.id, job.id)
    assert not unposted_job.is_live

    # Job is not available in search engine
    assert mock_algolia.search().hits == []

    # Check submission history
    submission = approval_repo.get_one(company_id=company.id, job_id=job.id)
    assert len(submission.history) == 4
    assert submission.history[0].approval_status == JobApprovalStatus.PENDING
    assert submission.history[1].approval_status == JobApprovalStatus.APPROVED
    assert submission.history[2].approval_status == JobApprovalStatus.POSTED
    assert submission.history[3].approval_status == JobApprovalStatus.UNPOSTED
    assert submission.current_approval_status == JobApprovalStatus.UNPOSTED


def test_job_submission_missing_fields(request_scope):
    company = CompanyFixture(request_scope).create_company()
    repo = JobRepository(request_scope, company.id)
    example_job = CreateJob(
        company_id=company.id,
        position_title="Software Engineer",
    )
    job = repo.create(example_job)
    usecase = JobUseCase(request_scope)
    with pytest.raises(FailedToPostJobException):
        usecase.submit_job_for_approval(company.id, job.id)


def test_job_submission_can_not_be_in_pending_status(request_scope):
    company_fixture = CompanyFixture(request_scope)
    user, company = company_fixture.create_company_with_owner()
    job = company_fixture.create_company_job(company.id)
    request_scope.user_id = user.id
    usecase = JobUseCase(request_scope)
    usecase.submit_job_for_approval(company.id, job.id)
    with pytest.raises(FailedToPostJobException):
        usecase.submit_job_for_approval(company.id, job.id)


def test_job_resubmission_updates_admin_approval_status(request_scope):
    job_approval_usecase = JobApprovalUseCase(request_scope)
    company_fixture = CompanyFixture(request_scope)
    user, company = company_fixture.create_company_with_owner()
    admin_user = UserFixture(request_scope).create_admin_user()
    request_scope.user_id = user.id
    job = company_fixture.create_company_job(company.id)
    usecase = JobUseCase(request_scope)
    submission = usecase.submit_job_for_approval(company.id, job.id)
    job_approval_usecase.update_job_approval_status(
        submission.id,
        admin_user.id,
        True,
        AdminCreateApprovalUpdate(
            approval_status=JobApprovalStatus.REJECTED, reason="Not good enough"
        ),
    )
    updated_submission = usecase.submit_job_for_approval(company.id, job.id)
    assert updated_submission.current_approval_status == JobApprovalStatus.RESUBMITTED


def test_submit_many_jobs(request_scope):
    company_fixture = CompanyFixture(request_scope)
    user, company = company_fixture.create_company_with_owner()
    request_scope.user_id = user.id
    job_1 = company_fixture.create_company_job(company.id)
    job_2 = company_fixture.create_company_job(company.id)

    usecase = JobUseCase(request_scope)
    errors = usecase.submit_many_jobs_for_approval(company.id, [job_1.id, job_2.id])
    assert not errors


def test_submit_many_jobs_with_some_errors(request_scope):
    company_fixture = CompanyFixture(request_scope)
    user, company = company_fixture.create_company_with_owner()
    request_scope.user_id = user.id
    job_1 = company_fixture.create_company_job(company.id)
    job_2 = company_fixture.create_company_job(company.id)
    job_3 = company_fixture.create_partial_job(company.id)

    usecase = JobUseCase(request_scope)
    errors = usecase.submit_many_jobs_for_approval(
        company.id, [job_1.id, job_2.id, job_3.id]
    )
    assert len(errors) == 1
    assert errors[0]["job_id"] == job_3.id
    assert "Missing job fields" in errors[0]["error"]


def test_remove_job_sumission(request_scope):
    company_fixture = CompanyFixture(request_scope)
    user, company = company_fixture.create_company_with_owner()
    request_scope.user_id = user.id
    job_1 = company_fixture.create_company_job(company.id)
    usecase = JobUseCase(request_scope)
    usecase.submit_job_for_approval(company.id, job_1.id)
    usecase.remove_job_submission(company.id, job_1.id)
    job_approval_repo = AdminJobApprovalRepository(request_scope)
    submission = job_approval_repo.get_one(company_id=company.id, job_id=job_1.id)
    assert submission.current_approval_status == JobApprovalStatus.REMOVED_BY_USER


def test_update_job_without_submission(request_scope):
    company_fixture = CompanyFixture(request_scope)
    user, company = company_fixture.create_company_with_owner()
    request_scope.user_id = user.id
    job_1 = company_fixture.create_company_job(company.id)

    job_usecase = JobUseCase(request_scope)
    updated_job = job_usecase.update_job(
        company.id,
        job_1.id,
        updates=UserCreateJob(description="nice job"),
        position_title="New Title",
    )

    assert updated_job.description == "nice job"
    assert updated_job.position_title == "New Title"


def test_update_job_with_submission(request_scope):
    company_fixture = CompanyFixture(request_scope)
    user, company = company_fixture.create_company_with_owner()
    admin_user = UserFixture(request_scope).create_admin_user()
    request_scope.user_id = user.id
    job_1 = company_fixture.create_company_job(company.id)

    job_usecase = JobUseCase(request_scope)
    job_1_submission = job_usecase.submit_job_for_approval(company.id, job_1.id)
    updated_job = job_usecase.update_job(
        company.id, job_1.id, position_title="New Title"
    )

    submission_repo = AdminJobApprovalRepository(request_scope)
    submission = submission_repo.get(job_1_submission.id)
    assert submission.current_approval_status == JobApprovalStatus.PENDING
    assert updated_job.position_title == "New Title"

    # Now admin approves and there's another update
    approval_usecase = JobApprovalUseCase(request_scope)
    approval_usecase.update_job_approval_status(
        job_1_submission.id,
        user_id=admin_user.id,
        is_admin_update=True,
        updates=AdminCreateApprovalUpdate(
            approval_status=JobApprovalStatus.APPROVED, reason="Looks good bro"
        ),
    )
    with pytest.raises(FailedToUpdateJobException):
        job_usecase.update_job(
            company.id, job_1.id, position_title="Different New Title"
        )


def test_job_model_Without_company_fields():
    job = UserCreateJob(position_title="Software Engineer", num_candidates_required=1)
    no_company_fields = job.get_without_company_fields()
    assert no_company_fields["position_title"] == "Software Engineer"
    assert "num_candidates_required" not in no_company_fields


def test_get_job_location_from_office_id(request_scope):
    # Create a job and use the office ID for the location
    company_fixture = CompanyFixture(request_scope)
    company = company_fixture.create_company()
    office = company_fixture.create_company_office(company.id)

    job_repo = JobRepository(request_scope, company.id)
    job = job_repo.create(
        CreateJob(
            company_id=company.id,
            position_title="Software Engineer",
            num_candidates_required=1,
            company_office_id=office.id,
        )
    )
    assert job.get_job_location(request_scope) == office.location


def test_job_without_location_or_office_returns_none(request_scope):
    job = Job(
        company_id="nice",
        id="abc",
        created_at=datetime.now(),
        created_by="abc",
        updated_at=datetime.now(),
        updated_by="abc",
        position_title="Nice",
    )
    assert job.get_job_location(request_scope) is None


def test_convert_to_algolia_record_with_missing_fields(request_scope):
    job = Job(
        company_id="nice",
        id="abc",
        created_at=datetime.now(),
        created_by="abc",
        updated_at=datetime.now(),
        updated_by="abc",
        position_title="Nice",
    )

    with pytest.raises(MissingJobFieldsException):
        AlgoliaJobRecord.convert_from_job_record(job, "abc", request_scope)


def test_convert_algolia_record_to_algolia_dict():
    record = AlgoliaJobRecord(
        job_id="abc",
        company_name="def",
        pay_max_as_hourly=123,
        pay_min_as_hourly=541,
        sub_categories=["one", "two"],
        category="nice",
        company_id="nice",
        position_title="Nice",
        description="Nice",
        schedule=ScheduleType.FULL_TIME,
        experience_required=ExperienceLevel.eleven_or_more_years,
        location_type=JobLocationType.REMOTE,
        required_job_skills=["Python"],
        background_check_required=True,
        drug_test_required=True,
    )
    algolia_dict = record.convert_to_algolia()
    from_algolia = AlgoliaJobRecord.convert_from_algolia(algolia_dict)
    assert from_algolia == record


def test_admin_approval_queries(request_scope):
    company_fixture = CompanyFixture(request_scope)
    user, company = company_fixture.create_company_with_owner()
    request_scope.user_id = user.id
    job_1 = company_fixture.create_company_job(company.id)
    job_2 = company_fixture.create_company_job(company.id)

    usecase = JobUseCase(request_scope)
    usecase.submit_many_jobs_for_approval(company.id, [job_1.id, job_2.id])

    approval_repo = AdminJobApprovalRepository(request_scope)
    all_approval_jobs, count = approval_repo.query_with_jobs()
    assert count == 2
    assert len(all_approval_jobs) == 2
    assert isinstance(all_approval_jobs[0], DataReducedAdminJobPostApproval)

    single_approval = approval_repo.get_with_job(all_approval_jobs[0].id)
    assert isinstance(single_approval, AdminJobPostApproval)
    assert single_approval.job is not None
    assert all_approval_jobs[0].job is not None
    assert single_approval.company is not None
    assert all_approval_jobs[0].company is not None
    assert single_approval.job.id == all_approval_jobs[0].job.id
    assert single_approval.company.id == all_approval_jobs[0].company.id


def test_get_jobs_with_companies(request_scope):
    data = ApplicationFixture(request_scope).create_application()
    repo = JobRepository(request_scope)

    results, count = repo.get_jobs_with_company()
    assert count == 1
    assert len(results) == 1

    assert results[0].id == data.job.id
    assert results[0].company.id == data.company.id


def test_get_jobs_with_applicants(request_scope):
    data = ApplicationFixture(request_scope).create_application()
    repo = JobRepository(request_scope)

    results, _ = repo.get_company_jobs(data.company.id)
    assert results[0].applicants == 1
    assert results[0].shortlisted_applicants == 0
