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
    JobSkill,
    ExperienceLevel,
    DataReducedCompany,
    JobLocationType,
)
from ajb.common.models import Location, convert_pay_to_hourly
from ajb.static.enumerations import PayType
from ajb.contexts.companies.offices.repository import OfficeRepository
from ajb.exceptions import MissingJobFieldsException
from ajb.vendor.arango.models import Filter, Operator, Sort

from ..enumerations import (
    ScheduleType,
    ResumeRequirement,
    WeeklyScheduleType,
    ShiftType,
)


class Pay(BaseModel):
    pay_type: PayType
    pay_min: int
    pay_max: int
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
        return convert_pay_to_hourly(self.pay_min, self.pay_type)

    @property
    def max_pay_as_hourly(self) -> float:
        return convert_pay_to_hourly(self.pay_min, self.pay_type)


class ApplicationSettings(BaseModel):
    let_candidates_contact_you_by_email: bool = True
    let_candidates_contact_you_by_phone: bool = True
    resume_requirement: ResumeRequirement = ResumeRequirement.required


class ApplicationQuestion(BaseModel):
    question: str
    answer_choices: list[str]
    deal_breaker: bool


class UserCreateJob(BaseModel):
    position_title: str | None = None
    description: str | None = None

    industry_category: str | None = None
    industry_subcategories: list[str] | None = None

    schedule: ScheduleType | None = None
    experience_required: ExperienceLevel | None = None

    location_type: JobLocationType | None = None
    location_override: Location | None = None
    company_office_id: str | None = None

    required_job_skills: t.List[JobSkill] | None = None
    on_job_training_offered: bool | None = None

    weekly_day_range: t.List[WeeklyScheduleType] | None = None
    shift_type: t.List[ShiftType] | None = None

    pay: Pay | None = None

    language_requirements: t.List[str] | None = None
    license_requirements: t.List[str] | None = None
    certification_requirements: t.List[str] | None = None

    background_check_required: bool | None = None
    drug_test_required: bool | None = None
    felons_accepted: bool | None = None
    disability_accepted: bool | None = None

    application_questions: t.List[ApplicationQuestion] | None = None
    desired_start_date: datetime | None = None

    job_main_image: str | None = None
    job_icon: str | None = None

    num_candidates_required: int | None = None
    ongoing_recruitment: bool | None = None
    ideal_days_to_hire: int | None = None
    internal_reference_code: str | None = None
    job_associated_company_description: str | None = None
    jog_tags: list[str] | None = None
    application_settings: ApplicationSettings | None = None
    position_filled: bool = False

    def get_without_company_fields(self):
        company_fields = {
            "num_candidates_required",
            "ongoing_recruitment",
            "ideal_days_to_hire",
            "internal_reference_code",
            "job_associated_company_description",
            "jog_tags",
            "application_settings",
            "application_questions",
            "desired_start_date",
        }
        return self.model_dump(exclude=company_fields)

    def calculate_score(self) -> float:
        weights = {
            "position_title": 10,
            "description": 10,
            "industry_category": 10,
            "schedule": 5,
            "experience_required": 6,
            "location_type": 10,
            "num_candidates_required": 3,
            "ongoing_recruitment": 2,
            "required_job_skills": 8,
            "on_job_training_offered": 2,
            "weekly_day_range": 3,
            "shift_type": 3,
            "pay": 5,
            "language_requirements": 4,
            "background_check_required": 2,
            "drug_test_required": 2,
            "felons_accepted": 2,
            "disability_accepted": 2,
            "ideal_days_to_hire": 2,
            "internal_reference_code": 1,
            "job_associated_company_description": 4,
            "application_settings": 3,
            "application_questions": 3,
            "desired_start_date": 3,
        }

        score = 0
        for attr, weight in weights.items():
            if getattr(self, attr):
                score += weight

        return score


class CreateJob(UserCreateJob):
    is_live: bool = False
    is_boosted: bool = False
    company_id: str
    job_score: float | None = None


class UpdateJob(UserCreateJob):
    is_live: bool | None = None
    is_boosted: bool | None = None
    position_title: str | None = None


class InternalUpdateJob(UpdateJob):
    position_filled: bool | None = None


class Job(CreateJob, BaseDataModel):
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

    def get_job_location(self, request_scope: RequestScope) -> Location | None:
        if self.location_override:
            return self.location_override
        if self.company_office_id:
            return (
                OfficeRepository(request_scope, self.company_id)
                .get(self.company_office_id)
                .location
            )
        return None

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


class AlgoliaJobRecord(BaseModel):
    """A flattened version of the Job model meant for Algolia searches"""

    job_id: str
    company_id: str
    company_name: str
    pay_min_as_hourly: float
    pay_max_as_hourly: float
    category: str
    sub_categories: list[str]
    position_title: str
    description: str
    schedule: ScheduleType
    experience_required: ExperienceLevel
    location_type: JobLocationType
    location: Location | None = None
    location_geo: dict[t.Literal["lat", "lng"], float | None] | None = None
    required_job_skills: list[str]
    background_check_required: bool
    drug_test_required: bool

    @classmethod
    def convert_from_job_record(
        cls, job: Job, company_name: str, request_scope: RequestScope
    ):
        missing_fields = job.get_missing_required_fields()
        if missing_fields:
            raise MissingJobFieldsException(fields=missing_fields)

        location = job.get_job_location(request_scope)
        assert job.pay
        assert job.experience_required
        assert job.schedule
        assert job.location_type
        assert job.industry_category
        assert job.industry_subcategories
        assert job.description
        assert job.required_job_skills
        assert job.background_check_required
        assert job.drug_test_required
        assert job.position_title

        return cls(
            job_id=job.id,
            company_id=job.company_id,
            company_name=company_name,
            pay_min_as_hourly=job.pay.min_pay_as_hourly,
            pay_max_as_hourly=job.pay.max_pay_as_hourly,
            category=job.industry_category,
            sub_categories=job.industry_subcategories,
            position_title=job.position_title,
            description=job.description,
            schedule=job.schedule,
            experience_required=job.experience_required,
            location_type=job.location_type,
            location=location,
            required_job_skills=[skill.skill_name for skill in job.required_job_skills],
            background_check_required=job.background_check_required,
            drug_test_required=job.drug_test_required,
            location_geo=(
                {"lat": location.lat, "lng": location.lng} if location else None
            ),
        )

    def convert_to_algolia(self):
        output = self.model_dump(mode="json")
        if self.location_geo and self.location_geo["lat"] and self.location_geo["lng"]:
            output["_geoloc"] = {
                "lat": self.location_geo["lat"],
                "lng": self.location_geo["lng"],
            }
        return output

    @classmethod
    def convert_from_algolia(cls, record: dict):
        return cls(
            job_id=record["job_id"],
            company_id=record["company_id"],
            company_name=record["company_name"],
            pay_min_as_hourly=record["pay_min_as_hourly"],
            pay_max_as_hourly=record["pay_max_as_hourly"],
            category=record["category"],
            sub_categories=record["sub_categories"],
            position_title=record["position_title"],
            description=record["description"],
            schedule=record["schedule"],
            experience_required=record["experience_required"],
            location_type=record["location_type"],
            location=(
                Location.model_validate(record["location"])
                if record["location"]
                else None
            ),
            required_job_skills=record["required_job_skills"],
            background_check_required=record["background_check_required"],
            drug_test_required=record["drug_test_required"],
            location_geo=record["_geoloc"] if "_geoloc" in record else None,
        )


@dataclass
class PaginatedJob(PaginatedResponse[Job]):
    data: list[Job]


class JobWithCandidates(BaseDataModel):
    position_title: str
    location: Location
    num_applicants: int
    num_shortlisted_applicants: int
    job_post_score: int
    job_status: str


@dataclass
class PaginatedJobsWithCandidates(PaginatedResponse[JobWithCandidates]):
    data: list[JobWithCandidates]


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
