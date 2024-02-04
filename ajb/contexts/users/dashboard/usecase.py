import typing as t
from datetime import datetime, timedelta

from ajb.base import BaseUseCase, Collection, RepoFilterParams, RequestScope
from ajb.base.events import CompanyEvent
from ajb.common.models import (
    TimeRange,
    TimesSeriesAverage,
    get_actions_as_daily_timeseries,
)
from ajb.contexts.applications.models import Application
from ajb.vendor.arango.models import Filter, Operator, Join
from ajb.utils import get_perecent

from .models import (
    UserDashboardSummary,
    UserDashboardApplicationJob,
    UserDashboardSavedJob,
    UserDashboardStatistics,
)

DEFAULT_TIME_DELTA = timedelta(days=30)


class UserDashboardUseCase(BaseUseCase):
    def __init__(
        self,
        request_scope: RequestScope,
        user_id: str,
        time_range: TimeRange = TimeRange(),
        averaging: TimesSeriesAverage = TimesSeriesAverage.HOURLY,
    ):
        super().__init__(request_scope)
        self.user_id = user_id
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

    def get_user_dashboard_summary(self) -> UserDashboardSummary:
        application_repo = self.get_repository(Collection.APPLICATIONS)
        all_user_applications, count = application_repo.query(user_id=self.user_id)
        casted_applications = t.cast(list[Application], all_user_applications)
        applications_with_views = [
            app for app in casted_applications if app.has_been_viewed_by_recruiters
        ]
        shortlisted_applications = [
            app for app in casted_applications if app.application_is_shortlisted
        ]
        return UserDashboardSummary(
            total_applications=count,
            applications_with_views=len(applications_with_views),
            applications_shortlisted=len(shortlisted_applications),
        )

    def get_user_dashboard_applied_jobs(
        self, query: RepoFilterParams = RepoFilterParams()
    ) -> tuple[list[UserDashboardApplicationJob], int]:
        query.filters.append(Filter(field="user_id", value=self.user_id))
        application_repo = self.get_repository(Collection.APPLICATIONS)
        results, count = application_repo.query_with_joins(
            joins=[
                Join(
                    to_collection_alias="company",
                    to_collection=Collection.COMPANIES.value,
                    from_collection_join_attr="company_id",
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
            UserDashboardApplicationJob.from_db_result(result) for result in results
        ]
        return formatted_results, count

    def get_user_dashboard_saved_jobs(
        self, query: RepoFilterParams = RepoFilterParams()
    ) -> tuple[list[UserDashboardSavedJob], int]:
        query.filters.append(Filter(field="user_id", value=self.user_id))
        user_saved_jobs_repo = self.get_repository(
            Collection.USER_SAVED_JOBS, self.request_scope, self.user_id
        )
        results, count = user_saved_jobs_repo.query_with_joins(
            joins=[
                Join(
                    to_collection_alias="company",
                    to_collection=Collection.COMPANIES.value,
                    from_collection_join_attr="company_id",
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
            UserDashboardSavedJob.from_db_result(result) for result in results
        ]
        return formatted_results, count

    def get_user_dashboard_statistics(
        self, query: RepoFilterParams | None = None
    ) -> UserDashboardStatistics:
        if not query:
            query = self._get_default_repo_params()
        company_action_repo = self.get_repository(Collection.COMPANY_ACTIONS)
        application_repo = self.get_repository(Collection.APPLICATIONS)
        application_count = application_repo.get_count(query, user_id=self.user_id)
        results, _ = company_action_repo.query(query, candidate_user_id=self.user_id)
        actions_as_timeseries = get_actions_as_daily_timeseries(results, self.averaging)
        action_summary = {
            key: sum(actions_as_timeseries.get(key, {}).values())
            for key in [
                CompanyEvent.COMPANY_VIEWS_CANDIDATES,
                CompanyEvent.COMPANY_CLICKS_CANDIDATE,
                CompanyEvent.COMPANY_SAVES_CANDIDATE,
                CompanyEvent.COMPANY_VIEWS_APPLICATIONS,
                CompanyEvent.COMPANY_CLICKS_ON_APPLICATION,
                CompanyEvent.COMPANY_SHORTLISTS_APPLICATION,
            ]
        }
        average_candidate_click_rate_percent = get_perecent(
            action_summary[CompanyEvent.COMPANY_CLICKS_CANDIDATE],
            action_summary[CompanyEvent.COMPANY_VIEWS_CANDIDATES],
        )
        average_candidate_save_rate_percent = get_perecent(
            action_summary[CompanyEvent.COMPANY_SAVES_CANDIDATE],
            action_summary[CompanyEvent.COMPANY_VIEWS_CANDIDATES],
        )
        average_application_view_rate_percent = get_perecent(
            action_summary[CompanyEvent.COMPANY_VIEWS_APPLICATIONS], application_count
        )
        average_application_click_rate_percent = get_perecent(
            action_summary[CompanyEvent.COMPANY_CLICKS_ON_APPLICATION],
            application_count,
        )
        average_application_shortlist_rate_percent = get_perecent(
            action_summary[CompanyEvent.COMPANY_SHORTLISTS_APPLICATION],
            application_count,
        )
        output = UserDashboardStatistics(
            total_profile_clicks=action_summary[CompanyEvent.COMPANY_CLICKS_CANDIDATE],
            total_profile_saves=action_summary[CompanyEvent.COMPANY_SAVES_CANDIDATE],
            total_applications=application_count,
            total_application_clicks=action_summary[
                CompanyEvent.COMPANY_CLICKS_ON_APPLICATION
            ],
            total_application_shortlists=action_summary[
                CompanyEvent.COMPANY_SHORTLISTS_APPLICATION
            ],
            average_profile_click_rate_percent=average_candidate_click_rate_percent,
            average_profile_save_rate_percent=average_candidate_save_rate_percent,
            profile_views_over_time=actions_as_timeseries.get(
                CompanyEvent.COMPANY_VIEWS_CANDIDATES, {}
            ),
            profile_saves_over_time=actions_as_timeseries.get(
                CompanyEvent.COMPANY_SAVES_CANDIDATE, {}
            ),
            average_application_view_rate_percent=average_application_view_rate_percent,
            average_application_click_rate_percent=average_application_click_rate_percent,
            average_application_shortlist_rate_percent=average_application_shortlist_rate_percent,
            application_views_over_time=actions_as_timeseries.get(
                CompanyEvent.COMPANY_VIEWS_APPLICATIONS, {}
            ),
            application_shortlists_over_time=actions_as_timeseries.get(
                CompanyEvent.COMPANY_SHORTLISTS_APPLICATION, {}
            ),
            applications_submitted_over_time=actions_as_timeseries.get(
                CompanyEvent.COMPANY_CLICKS_ON_APPLICATION, {}
            ),
        )
        output.recommendations = output.generate_recommendations()
        return output
