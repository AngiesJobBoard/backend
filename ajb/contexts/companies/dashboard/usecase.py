from datetime import datetime, timedelta

from ajb.base import (
    BaseUseCase,
    Collection,
    RepoFilterParams,
    RequestScope,
    Pagination,
)
from ajb.base.events import UserEvent
from ajb.common.models import (
    TimeRange,
    TimesSeriesAverage,
    get_actions_as_daily_timeseries,
)
from ajb.contexts.applications.repository import CompanyApplicationRepository
from ajb.vendor.arango.models import Filter, Operator, Join
from ajb.utils import get_perecent

from .models import (
    CompanyDashboardSummary,
    CompanyDashboardApplicant,
    CompanyDashboardJobPost,
    CompanyDashboardJobPostStatistics,
)

DEFAULT_TIME_DELTA = timedelta(days=30)
DEFAULT_TABLE_PAGE_SIZE = 10


class CompanyDashboardUseCase(BaseUseCase):
    def __init__(
        self,
        request_scope: RequestScope,
        company_id: str,
        time_range: TimeRange = TimeRange(),
        averaging: TimesSeriesAverage = TimesSeriesAverage.HOURLY,
    ):
        super().__init__(request_scope)
        self.company_id = company_id
        self.start = time_range.start or datetime.utcnow() - DEFAULT_TIME_DELTA
        self.end = time_range.end or datetime.utcnow() + timedelta(minutes=1)
        self.averaging = averaging

    def _get_default_repo_params(self) -> RepoFilterParams:
        return RepoFilterParams(
            filters=[
                Filter(
                    field="created_at",
                    operator=Operator.GREATER_THAN,
                    value=self.start.isoformat(),
                ),
                Filter(
                    field="created_at",
                    operator=Operator.LESS_THAN,
                    value=self.end.isoformat(),
                ),
            ],
            pagination=None,
        )

    def get_company_dashboard_summary(self) -> CompanyDashboardSummary:
        job_repo = self.get_repository(
            Collection.JOBS, self.request_scope, self.company_id
        )
        company_applicant_repo = CompanyApplicationRepository(self.request_scope)
        company_notification_repo = self.get_repository(
            Collection.COMPANY_NOTIFICATIONS, self.request_scope, self.company_id
        )
        job_count = job_repo.get_count()
        all_applicant_count = company_applicant_repo.get_application_count(
            self.company_id
        )
        new_applicant_count = company_applicant_repo.get_application_count(
            self.company_id, new_only=True
        )
        new_activity_updates = company_notification_repo.get_count(
            repo_filters=RepoFilterParams(filters=[Filter(field="is_new", value=True)])
        )
        return CompanyDashboardSummary(
            num_jobs_posted=job_count,
            total_applicants=all_applicant_count,
            num_new_applicants=new_applicant_count,
            num_activity_updates=new_activity_updates,
        )

    def get_company_dashboard_applicants(
        self, query: RepoFilterParams | None = None
    ) -> tuple[list[CompanyDashboardApplicant], int]:
        if not query:
            query = self._get_default_repo_params()
        query.pagination = Pagination(page_size=DEFAULT_TABLE_PAGE_SIZE)
        application_repo = self.get_repository(Collection.APPLICATIONS)
        results, count = application_repo.query_with_joins(
            joins=[
                Join(
                    to_collection_alias="user",
                    to_collection=Collection.USERS.value,
                    from_collection_join_attr="user_id",
                ),
                Join(
                    to_collection_alias="job",
                    to_collection=Collection.JOBS.value,
                    from_collection_join_attr="job_id",
                ),
            ],
            repo_filters=query,
        )
        formatted_results = [
            CompanyDashboardApplicant.from_db_result(result) for result in results
        ]
        return formatted_results, count

    def get_company_dashboard_job_posts(
        self, query: RepoFilterParams | None = None
    ) -> tuple[list[CompanyDashboardJobPost], int]:
        if query is None:
            query = self._get_default_repo_params()
        query.pagination = Pagination(page_size=DEFAULT_TABLE_PAGE_SIZE)
        job_repo = self.get_repository(
            Collection.JOBS, self.request_scope, self.company_id
        )
        results, count = job_repo.query_with_joins(
            joins=[
                Join(
                    to_collection_alias="application",
                    to_collection=Collection.APPLICATIONS.value,
                    from_collection_join_attr="_key",
                    to_collection_join_attr="job_id",
                    is_aggregate=True,
                )
            ],
            repo_filters=query,
        )
        formatted_results = [
            CompanyDashboardJobPost.from_db_result(result, self.request_scope)
            for result in results
        ]
        return formatted_results, count

    def get_company_job_post_statistics(
        self, query: RepoFilterParams | None = None
    ) -> CompanyDashboardJobPostStatistics:
        # Get impressions as timeseries
        if not query:
            query = self._get_default_repo_params()
        user_action_repo = self.get_repository(Collection.USER_ACTIONS)
        job_repo = self.get_repository(
            Collection.JOBS, self.request_scope, self.company_id
        )
        live_jobs = job_repo.get_count(repo_filters=query, is_live=True)
        results, _ = user_action_repo.query(
            repo_filters=query, company_id=self.company_id
        )
        actions_as_timeseries = get_actions_as_daily_timeseries(results, self.averaging)
        action_summary = {
            key: sum(actions_as_timeseries.get(key, {}).values())
            for key in [
                UserEvent.USER_VIEWS_JOBS,
                UserEvent.USER_CLICKS_JOB,
                UserEvent.USER_SAVES_JOB,
                UserEvent.USER_APPLIES_JOB,
            ]
        }
        average_click_rate_percent = get_perecent(
            action_summary[UserEvent.USER_CLICKS_JOB],
            action_summary[UserEvent.USER_VIEWS_JOBS],
        )
        average_save_rate_percent = get_perecent(
            action_summary[UserEvent.USER_SAVES_JOB],
            action_summary[UserEvent.USER_VIEWS_JOBS],
        )
        average_apply_rate_percent = get_perecent(
            action_summary[UserEvent.USER_APPLIES_JOB],
            action_summary[UserEvent.USER_VIEWS_JOBS],
        )
        output = CompanyDashboardJobPostStatistics(
            active_jobs=live_jobs,
            sum_job_views=action_summary[UserEvent.USER_VIEWS_JOBS],
            average_click_rate_percent=average_click_rate_percent,
            average_save_rate_percent=average_save_rate_percent,
            average_apply_rate_percent=average_apply_rate_percent,
            views_over_time=actions_as_timeseries.get(UserEvent.USER_VIEWS_JOBS, {}),
            clicks_over_time=actions_as_timeseries.get(UserEvent.USER_CLICKS_JOB, {}),
            saves_over_time=actions_as_timeseries.get(UserEvent.USER_SAVES_JOB, {}),
            applications_over_time=actions_as_timeseries.get(
                UserEvent.USER_APPLIES_JOB, {}
            ),
        )
        output.recommendations = output.generate_recommendation()
        return output
