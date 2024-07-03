from ajb.contexts.applications.models import CreateApplication
from ajb.contexts.applications.recruiter_updates.models import UpdateType
from ajb.contexts.applications.recruiter_updates.usecase import RecruiterUpdatesUseCase
from ajb.contexts.applications.usecase import ApplicationUseCase
from ajb.contexts.companies.jobs.models import UserCreateJob
from ajb.contexts.companies.jobs.usecase import JobsUseCase
from ajb.contexts.companies.models import ApplicationStatusRepresents
from ajb.contexts.companies.recruiters.repository import (
    RecruiterRepository,
    CreateRecruiter,
)
from ajb.contexts.companies.recruiters.models import RecruiterRole, RecruiterAndUser
from ajb.vendor.arango.models import Filter, Join
from ajb.base import RepoFilterParams

from ajb.fixtures.users import UserFixture
from ajb.fixtures.companies import CompanyFixture


def test_create_recruiter(request_scope):
    user = UserFixture(request_scope).create_user()
    company = CompanyFixture(request_scope).create_company()

    repo = RecruiterRepository(request_scope, company.id)
    res = repo.create(
        CreateRecruiter(
            company_id=company.id, user_id=user.id, role=RecruiterRole.OWNER
        )
    )
    assert res.role == RecruiterRole.OWNER

    edges, count = repo.query(user_id=user.id)
    assert count == 1
    assert len(edges) == 1
    assert edges[0].role == RecruiterRole.OWNER


def test_get_recruiters_by_company_id(request_scope):
    user = UserFixture(request_scope).create_user()
    company = CompanyFixture(request_scope).create_company()

    repo = RecruiterRepository(request_scope, company.id)
    repo.create(
        CreateRecruiter(
            company_id=company.id, user_id=user.id, role=RecruiterRole.OWNER
        )
    )

    repo.query_with_joins(
        joins=[
            Join(
                to_collection_alias="user",
                to_collection="users",
                from_collection_join_attr="user_id",
            )
        ],
        return_model=RecruiterAndUser,
    )


def test_get_single_recruiter(request_scope):
    user = UserFixture(request_scope).create_user()
    company = CompanyFixture(request_scope).create_company()

    repo = RecruiterRepository(request_scope, company.id)
    created_recruiter = repo.create(
        CreateRecruiter(
            company_id=company.id, user_id=user.id, role=RecruiterRole.OWNER
        )
    )

    single_recruiter = repo.get_one_with_joins(
        joins=[
            Join(
                to_collection_alias="user",
                to_collection="users",
                from_collection_join_attr="user_id",
            )
        ],
        return_model=RecruiterAndUser,
        repo_filters=RepoFilterParams(
            filters=[
                Filter(
                    collection_alias="user",
                    field="email",
                    value=user.email,
                )
            ]
        ),
    )
    single_recruiter_by_id = repo.get_with_joins(
        id=created_recruiter.id,
        joins=[
            Join(
                to_collection_alias="user",
                to_collection="users",
                from_collection_join_attr="user_id",
            )
        ],
        return_model=RecruiterAndUser,
    )

    assert single_recruiter == single_recruiter_by_id


def test_search_recruiters(request_scope):
    user = UserFixture(request_scope).create_user()
    company = CompanyFixture(request_scope).create_company()

    repo = RecruiterRepository(request_scope, company.id)
    repo.create(
        CreateRecruiter(
            company_id=company.id, user_id=user.id, role=RecruiterRole.OWNER
        )
    )

    results, count = repo.get_recruiters_by_company(
        company_id=company.id,
    )

    assert count == 1
    assert len(results) == 1


def test_recruiter_updates(request_scope, mock_openai):
    # Create recruiter
    usecase = RecruiterUpdatesUseCase(request_scope)
    user = UserFixture(request_scope).create_user()
    company = CompanyFixture(request_scope).create_company()

    repo = RecruiterRepository(request_scope, company.id)
    repo.create(
        CreateRecruiter(
            company_id=company.id, user_id=user.id, role=RecruiterRole.OWNER
        )
    )

    # Create job & application
    job_to_create = UserCreateJob(position_title="test")
    job = JobsUseCase(request_scope, mock_openai).create_job(company.id, job_to_create)

    application_usecase = ApplicationUseCase(request_scope)
    application = application_usecase.create_application(
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

    # Add comment
    usecase.add_recruiter_comment(
        company.id,
        job.id,
        application.id,
        user.id,
        "Apply guy is a great fit for this position.",
    )

    timeline = usecase.get_application_update_timeline(
        company.id, job.id, application.id
    )[0]
    assert (
        len(timeline) == 1
    )  # We should have one timeline entry from the add recruiter comment call
    assert timeline[0].type == UpdateType.NOTE
    assert timeline[0].comment == "Apply guy is a great fit for this position."

    # Update application status
    usecase.update_application_status(
        company.id,
        job.id,
        application.id,
        user.id,
        ApplicationStatusRepresents.INTERESTED,
        "I'd like to move forward to interview Apply guy",
    )

    timeline = usecase.get_application_update_timeline(
        company.id, job.id, application.id
    )[0]
    assert (
        len(timeline) == 2
    )  # We should have another entry in the timeline from changing the status

    # Find the new timeline entry (just in case the order in which they are returned is not deterministic)
    update_status_entry = 0
    if timeline[0].type == UpdateType.NOTE:
        # We are looking for the update status entry, so use the other one
        update_status_entry = 1

    # Check for update application status entry
    assert timeline[update_status_entry].type == UpdateType.STATUS_CHANGE
    assert (
        timeline[update_status_entry].new_application_status
        == ApplicationStatusRepresents.INTERESTED
    )
    assert (
        timeline[update_status_entry].comment
        == "I'd like to move forward to interview Apply guy"
    )
