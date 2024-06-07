import typing as t
from dataclasses import dataclass
from pydantic import BaseModel

from ajb.base.models import (
    BaseDataModel,
    PaginatedResponse,
    RepoFilterParams,
    Pagination,
)
from ajb.common.models import (
    ExperienceLevel,
    DataReducedCompany,
    JobLocationType,
)
from ajb.common.models import Location, Location
from ajb.vendor.arango.models import Filter, Operator, Sort

from ..enumerations import (
    ScheduleType,
)


class UserCreateJob(BaseModel):
    position_title: str | None = None
    description: str | None = None

    industry_category: str | None = None
    industry_subcategories: list[str] | None = None

    schedule: ScheduleType | None = None
    experience_required: ExperienceLevel | None = None

    location_type: JobLocationType | None = None
    location_override: Location | None = None

    required_job_skills: t.List[str] | None = None
    on_job_training_offered: bool | None = None

    application_questions_as_strings: list[str] | None = None

    language_requirements: t.List[str] | None = None
    license_requirements: t.List[str] | None = None
    certification_requirements: t.List[str] | None = None

    felons_accepted: bool | None = None
    disability_accepted: bool | None = None

    external_reference_code: str | None = None
    position_filled: bool = False


class CreateJob(UserCreateJob):
    company_id: str
    job_score: float | None = None
    job_score_reason: str | None = None
    total_applicants: int = 0
    high_matching_applicants: int = 0
    new_applicants: int = 0
    active: bool = True
    job_is_public: bool | None = None


class Job(CreateJob, BaseDataModel): ...


@dataclass
class PaginatedJob(PaginatedResponse[Job]):
    data: list[Job]


class AdminSearchJobsWithCompany(BaseModel):
    position_title: str | None = None
    company_name: str | None = None
    page: int = 0
    page_size: int = 25
    sort: str | None = None
    sort_is_descending: bool = False

    def convert_to_repo_params(self) -> RepoFilterParams:
        formatted_query = self.initialize_repo_params()
        self.add_filters(formatted_query)
        self.add_sorts(formatted_query)
        return formatted_query

    def initialize_repo_params(self) -> RepoFilterParams:
        return RepoFilterParams(
            filters=[],
            sorts=[],
            pagination=Pagination(page=self.page, page_size=self.page_size),
        )

    def add_filters(self, query: RepoFilterParams) -> None:
        if self.position_title:
            query.filters.append(
                Filter(
                    field="position_title",
                    value=self.position_title,
                    operator=Operator.CONTAINS,
                )
            )
        if self.company_name:
            query.filters.append(
                Filter(
                    field="name",
                    value=self.company_name,
                    operator=Operator.CONTAINS,
                    collection_alias="company",
                )
            )

    def add_sorts(self, query: RepoFilterParams) -> None:
        if self.sort:
            if "company" in self.sort:
                query.sorts.append(
                    Sort(
                        field="name",
                        direction="DESC" if self.sort_is_descending else "ASC",
                        collection_alias="company",
                    )
                )
            else:
                query.sorts.append(
                    Sort(
                        field=self.sort,
                        direction="DESC" if self.sort_is_descending else "ASC",
                    )
                )

    def sort_direction(self) -> str:
        return "DESC" if self.sort_is_descending else "ASC"


class JobWithCompany(BaseDataModel):
    position_title: str | None = None
    industry_category: str | None = None
    experience_required: ExperienceLevel | None = None
    job_score: float | None = None
    job_score_reason: str | None = None
    location_type: JobLocationType | None = None

    company: DataReducedCompany


@dataclass
class PaginatedJobsWithCompany(PaginatedResponse[JobWithCompany]):
    data: list[JobWithCompany]


class FullJobWithCompany(Job):
    company: DataReducedCompany
