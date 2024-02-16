from dataclasses import dataclass
from datetime import datetime
from pydantic import BaseModel, Field

from ajb.base.models import BaseDataModel, PaginatedResponse
from ajb.common.models import DataReducedJob, GeneralLocation
from ajb.contexts.users.models import User
from ajb.contexts.resumes.models import Resume

from .enumerations import ApplicationStatus


class DemographicData(BaseModel):
    birth_year: int | None = None
    has_disability: bool | None = None
    arrest_record: bool | None = None


class ContactInformation(BaseModel):
    user_location: GeneralLocation | None = None


class WorkHistory(BaseModel):
    job_title: str
    company_name: str
    job_industry: str | None = None
    still_at_job: bool | None = None
    start_date: str | datetime | None = None
    end_date: str | datetime | None = None


class Education(BaseModel):
    school_name: str
    level_of_education: str
    field_of_study: str
    still_in_school: bool | None = None
    start_date: str | datetime | None = None
    end_date: str | datetime | None = None


class Qualifications(BaseModel):
    most_recent_job: WorkHistory | None = None
    work_history: list[WorkHistory] | None = None
    education: list[Education] | None = None
    skills: list[str] | None = None
    licenses: list[str] | None = None
    certifications: list[str] | None = None
    language_proficiencies: list[str] | None = None

    def get_qualifications_score(self):
        """Returns a 0-100 score based on the details provided"""
        weights = {
            "most_recent_job": 40,
            "education": 25,
            "skills": 20,
            "licenses": 5,
            "certifications": 5,
            "language_proficiencies": 5,
        }

        score = 0
        for attr, weight in weights.items():
            if getattr(self, attr):
                score += weight

        return score


class UserCreatedApplication(BaseModel):
    applying_user_email: str
    company_id: str
    job_id: str
    resume_id: str | None = None
    cover_letter_content: str | None = None
    qualifications: Qualifications


class UserCreateRecruiterNote(BaseModel):
    note: str


class CreateRecruiterNote(UserCreateRecruiterNote):
    user_id: str


class RecruiterNote(CreateRecruiterNote):
    id: str
    created: datetime = Field(default_factory=datetime.utcnow)
    updated: datetime | None = None


class CreateApplicationStatusUpdate(BaseModel):
    status: ApplicationStatus
    update_reason: str


class ApplicationStatusRecord(CreateApplicationStatusUpdate):
    updated_by_user_id: str
    update_made_by_admin: bool


class CreateApplication(UserCreatedApplication):
    user_id: str
    application_status: ApplicationStatus

    application_status_history: list[ApplicationStatusRecord] = Field(
        default_factory=list
    )
    application_is_shortlisted: bool = False
    application_match_score: int = 0
    application_match_reason: str = ""

    recruiter_tags: list[str] = Field(default_factory=list)
    recruiter_notes: dict[str, RecruiterNote] = Field(default_factory=dict)


class Application(CreateApplication, BaseDataModel): ...


@dataclass
class PaginatedApplications(PaginatedResponse[Application]):
    data: list[Application]


class CompanyApplicationView(Application):
    user: User
    resume: Resume
    qualifications: Qualifications
    job: DataReducedJob


@dataclass
class PaginatedCompanyApplicationView(PaginatedResponse[CompanyApplicationView]):
    data: list[CompanyApplicationView]
