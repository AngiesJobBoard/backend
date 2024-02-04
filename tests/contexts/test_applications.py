from datetime import datetime
import pytest

from ajb.contexts.applications.repository import (
    UserApplicationRepository,
    CompanyApplicationRepository,
)
from ajb.contexts.applications.usecase import ApplicationsUseCase
from ajb.contexts.applications.models import (
    UserCreatedApplication,
    CreateRecruiterNote,
    CompanyApplicationView,
    UserApplicationView,
    ApplicationStatusRecord,
    ApplicationStatus,
)
from ajb.exceptions import EntityNotFound

from ajb.fixtures.companies import CompanyFixture
from ajb.fixtures.users import UserFixture
from ajb.fixtures.applications import ApplicationFixture


def test_basic_application(request_scope):
    company_fixture = CompanyFixture(request_scope)
    _, company = company_fixture.create_company_with_owner()
    job = company_fixture.create_company_job(company.id)

    user_fixture = UserFixture(request_scope)
    applying_user = user_fixture.create_user(email="apply@email.com")
    resume = user_fixture.create_resume_for_user(applying_user.id)

    usecase = ApplicationsUseCase(request_scope)
    usecase.user_creates_application(
        applying_user.id,
        UserCreatedApplication(
            company_id=company.id,
            job_id=job.id,
            resume_id=resume.id,
        ),
    )


def test_application_queries(request_scope):
    application_data = ApplicationFixture(request_scope).create_application()
    request_scope.company_id = application_data.company.id
    user_repo = UserApplicationRepository(request_scope)
    company_repo = CompanyApplicationRepository(request_scope)

    # Test user query
    user_list_results, count = user_repo.get_candidate_view_list(
        application_data.user.id
    )
    assert count == 1
    assert len(user_list_results) == 1
    assert isinstance(user_list_results[0], UserApplicationView)

    # Test user get
    single_user_result = user_repo.get_candidate_view_single(
        application_data.user.id, application_data.application.id
    )
    assert single_user_result == user_list_results[0]
    assert isinstance(single_user_result, UserApplicationView)

    # # Test company query
    company_list_results, count = company_repo.get_company_view_list(
        application_data.company.id
    )
    assert count == 1
    assert len(company_list_results) == 1
    assert isinstance(company_list_results[0], CompanyApplicationView)

    # # Test company get
    single_company_result = company_repo.get_company_view_single(
        application_data.company.id, application_data.application.id
    )
    assert single_company_result == company_list_results[0]
    assert isinstance(single_company_result, CompanyApplicationView)


def test_recruiter_notes(request_scope):
    application_data = ApplicationFixture(request_scope).create_application()
    company_repo = CompanyApplicationRepository(request_scope)

    assert len(application_data.application.recruiter_notes) == 0
    response = company_repo.create_recruiter_note(
        application_data.company.id,
        application_data.application.id,
        CreateRecruiterNote(
            note="Good looking candidate", user_id=application_data.admin.id
        ),
    )
    assert len(response.recruiter_notes) == 1

    application = company_repo.get(application_data.application.id)
    assert len(application.recruiter_notes) == 1

    response_next = company_repo.create_recruiter_note(
        application_data.company.id,
        application_data.application.id,
        CreateRecruiterNote(
            note="Not a good fit, IMO", user_id=application_data.admin.id
        ),
    )
    assert len(response_next.recruiter_notes) == 2

    created_note_id = list(response.recruiter_notes.keys())[0]
    response = company_repo.update_recruiter_note(
        application_data.company.id,
        application_data.application.id,
        created_note_id,
        CreateRecruiterNote(
            note="Good looking candidate, but not a good fit",
            user_id=application_data.admin.id,
        ),
    )
    assert len(response.recruiter_notes) == 2

    application = company_repo.get(application_data.application.id)
    assert len(application.recruiter_notes) == 2

    response = company_repo.delete_recruiter_note(
        application_data.company.id, application_data.application.id, created_note_id
    )
    assert response is True

    application = company_repo.get(application_data.application.id)
    assert len(application.recruiter_notes) == 1


def test_status_change_and_history(request_scope):
    application_data = ApplicationFixture(request_scope).create_application()
    company_repo = CompanyApplicationRepository(request_scope)

    assert len(application_data.application.application_status_history) == 0

    response = company_repo.update_application_status(
        application_data.company.id,
        application_data.application.id,
        ApplicationStatusRecord(
            status=ApplicationStatus.IN_REVIEW_BY_ADMIN,
            updated_by_user_id=application_data.user.id,
            update_made_by_admin=True,
            update_reason="Checking by Admin",
        ),
    )

    assert len(response.application_status_history) == 1
    assert (
        response.application_status_history[0].status
        == ApplicationStatus.IN_REVIEW_BY_ADMIN
    )


def test_company_get_application_not_exist(request_scope):
    application_data = ApplicationFixture(request_scope).create_application()
    company_repo = CompanyApplicationRepository(request_scope)

    with pytest.raises(EntityNotFound):
        company_repo._company_get_application(application_data.company.id, "not_found")


def test_company_updates_application(request_scope):
    application_data = ApplicationFixture(request_scope).create_application()
    request_scope.company_id = application_data.company.id
    company_repo = CompanyApplicationRepository(request_scope)

    company_repo.company_updates_application_shortlist(
        application_data.company.id, application_data.application.id, True
    )
    application = company_repo.get(application_data.application.id)
    assert application.application_is_shortlisted is True

    company_repo.company_updates_application_shortlist(
        application_data.company.id, application_data.application.id, False
    )
    application = company_repo.get(application_data.application.id)
    assert application.application_is_shortlisted is False


def test_company_update_recruiter_note_not_found(request_scope):
    application_data = ApplicationFixture(request_scope).create_application()
    company_repo = CompanyApplicationRepository(request_scope)

    with pytest.raises(EntityNotFound):
        company_repo.update_recruiter_note(
            application_data.company.id,
            application_data.application.id,
            "not_found",
            CreateRecruiterNote(
                note="Good looking candidate", user_id=application_data.admin.id
            ),
        )


def test_company_delete_recruiter_note_not_found(request_scope):
    application_data = ApplicationFixture(request_scope).create_application()
    company_repo = CompanyApplicationRepository(request_scope)

    with pytest.raises(EntityNotFound):
        company_repo.delete_recruiter_note(
            application_data.company.id,
            application_data.application.id,
            "not_found",
        )


def test_update_application_status_to_rejected(request_scope):
    application_data = ApplicationFixture(request_scope).create_application()
    request_scope.company_id = application_data.company.id
    company_repo = CompanyApplicationRepository(request_scope)

    company_repo.update_application_status(
        application_data.company.id,
        application_data.application.id,
        ApplicationStatusRecord(
            status=ApplicationStatus.REJECTED_BY_COMPANY,
            updated_by_user_id=application_data.user.id,
            update_made_by_admin=True,
            update_reason="",
        ),
    )


def test_company_view_list_shortlist_only(request_scope):
    application_data = ApplicationFixture(request_scope).create_application()
    request_scope.company_id = application_data.company.id
    company_repo = CompanyApplicationRepository(request_scope)

    results, count = company_repo.get_company_view_list(
        application_data.company.id,
        shortlist_only=True,
    )
    assert count == 0
    assert len(results) == 0

    company_repo.company_updates_application_shortlist(
        application_data.company.id, application_data.application.id, True
    )

    results, count = company_repo.get_company_view_list(
        application_data.company.id,
        shortlist_only=True,
    )
    assert count == 1
    assert len(results) == 1


def test_company_application_view_not_found(request_scope):
    application_data = ApplicationFixture(request_scope).create_application()
    company_repo = CompanyApplicationRepository(request_scope)

    with pytest.raises(EntityNotFound):
        company_repo.get_company_view_single(
            application_data.company.id,
            "not_found",
        )


def test_get_application_count_with_date_filters(request_scope):
    application_data = ApplicationFixture(request_scope).create_application()
    company_repo = CompanyApplicationRepository(request_scope)

    start_only_results = company_repo.get_application_count(
        company_id=application_data.company.id, start_date_filter=datetime(2020, 1, 1)
    )
    end_only_results = company_repo.get_application_count(
        company_id=application_data.company.id, end_date_filter=datetime(3020, 1, 1)
    )
    both_results = company_repo.get_application_count(
        company_id=application_data.company.id,
        start_date_filter=datetime(2020, 1, 1),
        end_date_filter=datetime(3020, 1, 1),
    )
    assert start_only_results == end_only_results == both_results == 1

    no_data_filter = company_repo.get_application_count(
        company_id=application_data.company.id,
        start_date_filter=datetime(2020, 1, 1),
        end_date_filter=datetime(2020, 1, 1),
    )
    assert no_data_filter == 0


def test_user_get_application_not_found(request_scope):
    application_data = ApplicationFixture(request_scope).create_application()
    user_repo = UserApplicationRepository(request_scope)

    with pytest.raises(EntityNotFound):
        user_repo.get_candidate_view_single(
            application_data.user.id,
            "not_found",
        )


def test_candidate_updates_application(request_scope):
    application_data = ApplicationFixture(request_scope).create_application()
    user_repo = UserApplicationRepository(request_scope)

    user_repo.candidate_updates_application(
        application_data.user.id,
        application_data.application.id,
        new_status=ApplicationStatus.WITHDRAWN_BY_USER,  # type: ignore
    )


def test_candidate_view_single_application_not_found(request_scope):
    application_data = ApplicationFixture(request_scope).create_application()
    user_repo = UserApplicationRepository(request_scope)

    with pytest.raises(EntityNotFound):
        user_repo.get_candidate_view_single(
            application_data.user.id,
            "not_found",
        )
