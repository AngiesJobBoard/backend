import typing as t
from dataclasses import dataclass
from datetime import datetime
from pydantic import BaseModel

from ajb.base.models import (
    BaseDataModel,
    PaginatedResponse,
    RequestScope,
    RepoFilterParams,
    Pagination,
)
from ajb.common.models import (
    ExperienceLevel,
    DataReducedCompany,
    JobLocationType,
)
from ajb.common.models import Location, Location, convert_pay_to_hourly, ApplicationQuestion
from ajb.static.enumerations import PayType
from ajb.exceptions import MissingJobFieldsException
from ajb.vendor.arango.models import Filter, Operator, Sort

from ..enumerations import (
    ScheduleType,
    WeeklyScheduleType,
    ShiftType,
)


class Pay(BaseModel):
    pay_type: PayType = PayType.YEARLY
    pay_min: int | None = None
    pay_max: int | None = None
    exact_pay: int | None = None
    includes_bonus: bool | None = None
    includes_commission: bool | None = None
    includes_equity: bool | None = None
    includes_tips: bool | None = None
    includes_vacation: bool | None = None
    included_vacation_days: int | None = None
    includes_relocation: bool | None = None
    max_included_relocation_amount: int | None = None
    includes_signing_bonus: bool | None = None
    max_included_signing_bonus_amount: int | None = None

    @property
    def min_pay_as_hourly(self) -> float:
        if not self.pay_min:
            return 0
        return convert_pay_to_hourly(self.pay_min, self.pay_type)

    @property
    def max_pay_as_hourly(self) -> float:
        if not self.pay_max:
            return 0
        return convert_pay_to_hourly(self.pay_max, self.pay_type)


class UserCreateJob(BaseModel):
    position_title: str | None = None
    description: str | None = None

    industry_category: str | None = None
    industry_subcategories: list[str] | None = None

    schedule: ScheduleType | None = None
    experience_required: ExperienceLevel | None = None

    location_type: JobLocationType | None = None
    location_override: Location | Location | None = None
    company_office_id: str | None = None

    required_job_skills: t.List[str] | None = None
    on_job_training_offered: bool | None = None

    weekly_day_range: t.List[WeeklyScheduleType] | None = None
    shift_type: t.List[ShiftType] | None = None

    pay: Pay | None = None

    application_questions_as_strings: list[str] | None = None

    language_requirements: t.List[str] | None = None
    license_requirements: t.List[str] | None = None
    certification_requirements: t.List[str] | None = None

    background_check_required: bool | None = None
    drug_test_required: bool | None = None
    felons_accepted: bool | None = None
    disability_accepted: bool | None = None

    desired_start_date: datetime | None = None

    job_main_image: str | None = None
    job_icon: str | None = None

    num_candidates_required: int | None = None
    ongoing_recruitment: bool | None = None
    ideal_days_to_hire: int | None = None
    internal_reference_code: str | None = None
    job_associated_company_description: str | None = None
    job_tags: list[str] | None = None
    position_filled: bool = False

    def get_without_company_fields(self):
        company_fields = {
            "num_candidates_required",
            "ongoing_recruitment",
            "ideal_days_to_hire",
            "internal_reference_code",
            "job_tags",
            "desired_start_date",
        }
        return self.model_dump(exclude=company_fields)

    def calculate_score(self) -> float:
        weights = {
            "position_title": 10,
            "description": 10,
            "industry_category": 13,
            "schedule": 5,
            "experience_required": 6,
            "location_type": 10,
            "num_candidates_required": 3,
            "ongoing_recruitment": 2,
            "required_job_skills": 8,
            "on_job_training_offered": 2,
            "weekly_day_range": 3,
            "shift_type": 3,
            "pay": 8,
            "language_requirements": 4,
            "background_check_required": 2,
            "drug_test_required": 2,
            "felons_accepted": 2,
            "disability_accepted": 2,
            "ideal_days_to_hire": 2,
            "internal_reference_code": 1,
            "job_associated_company_description": 4,
            "desired_start_date": 3,
        }

        score = 0
        for attr, weight in weights.items():
            if getattr(self, attr):
                score += weight

        return score

    @classmethod
    def from_csv(cls, values: dict) -> "UserCreateJob":
        values["industry_subcategories"] = values.get(
            "industry_subcategories", ""
        ).split(",")
        values["required_job_skills"] = values.get("required_job_skills", "").split(",")
        values["weekly_day_range"] = values.get("weekly_day_range", "").split(",")
        values["shift_type"] = values.get("shift_type", "").split(",")
        values["language_requirements"] = values.get("language_requirements", "").split(
            ","
        )
        values["license_requirements"] = values.get("license_requirements", "").split(
            ","
        )
        values["certification_requirements"] = values.get(
            "certification_requirements", ""
        ).split(",")

        if values.get("zipcode"):
            values["location_override"] = Location(
                zipcode=str(values.get("zipcode")),
            )
        return cls(**values)


class CreateJob(UserCreateJob):
    company_id: str
    job_score: float | None = None
    total_applicants: int = 0
    high_matching_applicants: int = 0
    shortlisted_applicants: int = 0
    new_applicants: int = 0


class Job(CreateJob, BaseDataModel):
    applicants: int = 0
    shortlisted_applicants: int = 0

    @property
    def required_fields(self):
        return [
            "position_title",
            "description",
            "industry_category",
            "schedule",
            "location_type",
            "required_job_skills",
            "pay",
            "background_check_required",
            "drug_test_required",
            "experience_required",
        ]

    def get_missing_required_fields(self):
        return [
            field
            for field in self.required_fields
            if not getattr(self, field)
            or getattr(self, field) == []
            or getattr(self, field) == {}
        ]

    def check_for_missing_fields(self):
        missing_fields = self.get_missing_required_fields()
        if missing_fields:
            raise MissingJobFieldsException(fields=missing_fields)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.job_score = self.calculate_score()


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
        formatted_query = RepoFilterParams(
            filters=[],
            sorts=[],
            pagination=Pagination(
                page=self.page,
                page_size=self.page_size,
            ),
        )
        if self.position_title:
            formatted_query.filters.append(
                Filter(
                    field="position_title",
                    value=self.position_title,
                    operator=Operator.CONTAINS,
                )
            )
        if self.company_name:
            formatted_query.filters.append(
                Filter(
                    field="name",
                    value=self.company_name,
                    operator=Operator.CONTAINS,
                    collection_alias="company",
                )
            )
        if self.sort:
            if "company" in self.sort:
                formatted_query.sorts.append(
                    Sort(
                        field="name",
                        direction="DESC" if self.sort_is_descending else "ASC",
                        collection_alias="company",
                    )
                )
            elif "pay" in self.sort:
                formatted_query.sorts.append(
                    Sort(
                        field=self.sort.replace("__", "."),
                        direction="DESC" if self.sort_is_descending else "ASC",
                    )
                )
            else:
                formatted_query.sorts.append(
                    Sort(
                        field=self.sort,
                        direction="DESC" if self.sort_is_descending else "ASC",
                    )
                )
        return formatted_query


class JobWithCompany(BaseDataModel):
    position_title: str | None = None
    industry_category: str | None = None
    pay: Pay | None = None
    desired_start_date: datetime | None = None
    experience_required: ExperienceLevel | None = None
    is_live: bool = False
    is_boosted: bool = False
    job_score: float | None = None
    location_type: JobLocationType | None = None

    company: DataReducedCompany


@dataclass
class PaginatedJobsWithCompany(PaginatedResponse[JobWithCompany]):
    data: list[JobWithCompany]
