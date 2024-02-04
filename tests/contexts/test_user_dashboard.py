from ajb.base.events import CompanyEvent
from ajb.contexts.users.dashboard.usecase import UserDashboardUseCase
from ajb.contexts.companies.actions.repository import CompanyActionRepository
from ajb.contexts.companies.actions.models import CreateCompanyAction
from ajb.contexts.applications.repository import ApplicationRepository
from ajb.contexts.users.saved_jobs.repository import (
    UserSavedJobsRepository,
    CreateSavedJob,
)

from ajb.fixtures.applications import ApplicationFixture


def test_user_dashboard_summary(request_scope):
    application_data = ApplicationFixture(request_scope).create_application()
    usecase = UserDashboardUseCase(
        request_scope,
        application_data.user.id,
    )

    results = usecase.get_user_dashboard_summary()
    assert results.total_applications == 1
    assert results.applications_with_views == 0
    assert results.applications_shortlisted == 0

    ApplicationRepository(request_scope).update_fields(
        application_data.application.id,
        has_been_viewed_by_recruiters=True,
        application_is_shortlisted=True,
    )

    results = usecase.get_user_dashboard_summary()
    assert results.total_applications == 1
    assert results.applications_with_views == 1
    assert results.applications_shortlisted == 1


def test_user_dashboard_applied_jobs(request_scope):
    application_data = ApplicationFixture(request_scope).create_application()
    usecase = UserDashboardUseCase(
        request_scope,
        application_data.user.id,
    )

    usecase.get_user_dashboard_applied_jobs()


def test_user_dashboard_saved_jobs(request_scope):
    application_data = ApplicationFixture(request_scope).create_application()
    usecase = UserDashboardUseCase(
        request_scope,
        application_data.user.id,
    )
    UserSavedJobsRepository(request_scope, application_data.user.id).create(
        CreateSavedJob(
            job_id=application_data.job.id,
            company_id=application_data.company.id,
        )
    )
    usecase.get_user_dashboard_saved_jobs()


def test_get_user_dashboard_profile_activity(request_scope):
    application_data = ApplicationFixture(request_scope).create_application()
    usecase = UserDashboardUseCase(
        request_scope,
        application_data.user.id,
    )
    for _ in range(10):
        CompanyActionRepository(request_scope).create(
            CreateCompanyAction(
                action=CompanyEvent.COMPANY_CLICKS_CANDIDATE,
                candidate_user_id=application_data.user.id,
                company_id=application_data.company.id,
            )
        )
    for _ in range(5):
        CompanyActionRepository(request_scope).create(
            CreateCompanyAction(
                action=CompanyEvent.COMPANY_SAVES_CANDIDATE,
                candidate_user_id=application_data.user.id,
                company_id=application_data.company.id,
            )
        )
    usecase.get_user_dashboard_statistics()
