from ajb.base.events import UserEvent
from ajb.contexts.companies.dashboard.usecase import CompanyDashboardUseCase
from ajb.contexts.users.actions.repository import UserActionRepository
from ajb.contexts.users.actions.models import CreateUserAction

from ajb.fixtures.applications import ApplicationFixture


def test_company_dashboard_summary(request_scope):
    application_data = ApplicationFixture(request_scope).create_application()
    usecase = CompanyDashboardUseCase(
        request_scope=request_scope,
        company_id=application_data.company.id,
    )

    usecase.get_company_dashboard_summary()


def test_company_dashboard_applicants(request_scope):
    application_data = ApplicationFixture(request_scope).create_application()
    usecase = CompanyDashboardUseCase(
        request_scope=request_scope,
        company_id=application_data.company.id,
    )

    usecase.get_company_dashboard_applicants()


def test_company_job_posts(request_scope):
    application_data = ApplicationFixture(request_scope).create_application()
    request_scope.company_id = application_data.company.id
    usecase = CompanyDashboardUseCase(
        request_scope=request_scope,
        company_id=application_data.company.id,
    )

    results, count = usecase.get_company_dashboard_job_posts()
    assert count == 1
    assert results[0].total_num_applicants == 1


def test_company_job_post_statistics(request_scope):
    application_data = ApplicationFixture(request_scope).create_application()
    usecase = CompanyDashboardUseCase(
        request_scope=request_scope,
        company_id=application_data.company.id,
    )

    # Add some views and clicks
    user_action_repo = UserActionRepository(request_scope)
    for _ in range(10):
        user_action_repo.create(
            CreateUserAction(
                action=UserEvent.USER_VIEWS_JOBS,
                job_id=application_data.job.id,
                company_id=application_data.company.id,
                user_is_anonymous=False,
            )
        )
    for _ in range(5):
        user_action_repo.create(
            CreateUserAction(
                action=UserEvent.USER_CLICKS_JOB,
                job_id=application_data.job.id,
                company_id=application_data.company.id,
                user_is_anonymous=False,
            )
        )
    user_action_repo.create(
        CreateUserAction(
            action=UserEvent.USER_APPLIES_JOB,
            job_id=application_data.job.id,
            company_id=application_data.company.id,
            user_is_anonymous=False,
        )
    )

    results = usecase.get_company_job_post_statistics()
    assert results.sum_job_views == 10
    assert results.average_click_rate_percent == 50
    assert results.average_apply_rate_percent == 10
