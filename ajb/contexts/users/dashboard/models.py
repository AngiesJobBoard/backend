from dataclasses import dataclass
from datetime import datetime
from pydantic import BaseModel

from ajb.base import BaseDataModel, PaginatedResponse
from ajb.common.models import DataReducedCompany, DataReducedJob
from ajb.contexts.applications.models import Application
from ajb.contexts.users.saved_jobs.models import SavedJob


class UserDashboardSummary(BaseModel):
    total_applications: int
    applications_with_views: int
    applications_shortlisted: int


class UserDashboardApplicationJob(BaseDataModel):
    job: DataReducedJob
    company: DataReducedCompany
    application_is_shortlisted: bool
    application_match_score: int

    @classmethod
    def from_db_result(cls, result: dict):
        company = result.pop("company")
        job = result.pop("job")
        application = Application.from_arango(result)

        return cls(
            **application.model_dump(),
            job=DataReducedJob.model_validate(job),
            company=DataReducedCompany.model_validate(company),
        )


class UserDashboardSavedJob(BaseDataModel):
    """Base Data is that of the saved job"""

    job: DataReducedJob
    company: DataReducedCompany

    @classmethod
    def from_db_result(cls, result: dict):
        company = result.pop("company")
        job = result.pop("job")
        saved_job = SavedJob.from_arango(result)

        return cls(
            **saved_job.model_dump(),
            job=DataReducedJob.model_validate(job),
            company=DataReducedCompany.model_validate(company),
        )


@dataclass
class PaginatedUserDashboardApplicationJob(
    PaginatedResponse[UserDashboardApplicationJob]
):
    data: list[UserDashboardApplicationJob]


@dataclass
class PaginatedUserDashboardSavedJob(PaginatedResponse[UserDashboardSavedJob]):
    data: list[UserDashboardSavedJob]


class UserDashboardStatistics(BaseModel):
    total_profile_clicks: int
    total_profile_saves: int

    total_applications: int
    total_application_clicks: int
    total_application_shortlists: int

    average_profile_click_rate_percent: int
    average_profile_save_rate_percent: int

    profile_views_over_time: dict[datetime, int]
    profile_saves_over_time: dict[datetime, int]

    average_application_view_rate_percent: int
    average_application_click_rate_percent: int
    average_application_shortlist_rate_percent: int

    application_views_over_time: dict[datetime, int]
    application_shortlists_over_time: dict[datetime, int]
    applications_submitted_over_time: dict[datetime, int]

    recommendations: str | None = None

    def generate_recommendations(self):
        return "No Recommendations"
