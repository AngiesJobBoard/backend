from dataclasses import dataclass
from datetime import datetime
from pydantic import BaseModel

from ajb.base import BaseDataModel, PaginatedResponse, RequestScope
from ajb.common.models import Location
from ajb.contexts.admin.jobs.models import Job
from ajb.contexts.applications.models import ApplicationStatus
from ajb.utils import get_nested_value


DEFAULT_EMPTY_VALUE = " - "


class CompanyDashboardSummary(BaseModel):
    num_jobs_posted: int
    total_applicants: int
    num_new_applicants: int
    num_activity_updates: int


class CompanyDashboardApplicant(BaseDataModel):
    """Base of this is the application, it is joined with the user table"""

    image_url: str
    first_name: str
    last_name: str
    city: str = DEFAULT_EMPTY_VALUE
    last_job_title: str = DEFAULT_EMPTY_VALUE
    last_job_company: str = DEFAULT_EMPTY_VALUE
    position_applied_for: str
    current_status: ApplicationStatus
    application_match_score: int

    @classmethod
    def from_db_result(cls, result: dict) -> "CompanyDashboardApplicant":
        user_result = result.get("user", {})
        job_result = result.get("job", {})

        city = get_nested_value(
            user_result, ["contact_information", "user_location", "city"]
        )
        last_job_title = get_nested_value(
            user_result, ["qualifications", "most_recent_job", "job_title"]
        )
        last_job_company = get_nested_value(
            user_result, ["qualifications", "most_recent_job", "company_name"]
        )

        return cls(
            id=result["_id"],
            created_at=result["created_at"],
            updated_at=result["updated_at"],
            created_by=result["created_by"],
            updated_by=result["updated_by"],
            image_url=user_result.get("image_url"),
            first_name=user_result.get("first_name"),
            last_name=user_result.get("last_name"),
            city=str(city) if city else DEFAULT_EMPTY_VALUE,
            last_job_title=(
                str(last_job_title) if last_job_title else DEFAULT_EMPTY_VALUE
            ),
            last_job_company=(
                str(last_job_company) if last_job_company else DEFAULT_EMPTY_VALUE
            ),
            position_applied_for=job_result.get("position_title"),
            current_status=result["application_status"],
            application_match_score=result["application_match_score"],
        )


@dataclass
class PaginatedDashboardApplicants(PaginatedResponse[CompanyDashboardApplicant]):
    data: list[CompanyDashboardApplicant]


class CompanyDashboardJobPost(BaseDataModel):
    """Base object is the job"""

    job_icon: str | None
    position_title: str
    location: Location | None
    job_score: float
    is_live: bool
    is_boosted: bool

    total_num_applicants: int
    num_shortlisted_candidates: int

    @classmethod
    def from_db_result(
        cls, result: dict, request_scope: RequestScope
    ) -> "CompanyDashboardJobPost":
        applications = result.pop("application")
        job = Job.from_arango(result)

        total_applicants = len(applications)
        total_shortlisted = len(
            [app for app in applications if app["application_is_shortlisted"]]
        )
        return cls(
            id=job.id,
            created_at=job.created_at,
            updated_at=job.updated_at,
            created_by=job.created_by,
            updated_by=job.updated_by,
            job_icon=job.job_icon,
            position_title=str(job.position_title),
            location=job.get_job_location(request_scope),
            job_score=job.job_score or 0,
            is_live=job.is_live,
            is_boosted=job.is_boosted,
            total_num_applicants=total_applicants,
            num_shortlisted_candidates=total_shortlisted,
        )


@dataclass
class PaginatedCompanyDashboardJobs(PaginatedResponse[CompanyDashboardJobPost]):
    data: list[CompanyDashboardJobPost]


class CompanyDashboardJobPostStatistics(BaseModel):
    active_jobs: int
    sum_job_views: int
    average_click_rate_percent: int
    average_save_rate_percent: int
    average_apply_rate_percent: int

    views_over_time: dict[datetime, int]
    clicks_over_time: dict[datetime, int]
    saves_over_time: dict[datetime, int]
    applications_over_time: dict[datetime, int]

    recommendations: str | None = None

    def generate_recommendation(self):
        return "No Recommendations"


class CompanyDashboardBudgetSummary(BaseModel):
    total_spend: int
