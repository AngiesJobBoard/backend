from dataclasses import dataclass
from datetime import datetime
from pydantic import BaseModel, Field

from ajb.base.models import BaseDataModel, PaginatedResponse
from ajb.common.models import DataReducedCompany, DataReducedJob, JobNameOnly
from ajb.contexts.users.models import User, AlgoliaCandidateSearch
from ajb.contexts.users.resumes.models import Resume

from .enumerations import ApplicationStatus


class UserCreatedApplication(BaseModel):
    company_id: str
    job_id: str
    resume_id: str
    cover_letter_content: str | None = None


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

    has_been_viewed_by_recruiters: bool = False
    recruiter_tags: list[str] = Field(default_factory=list)
    recruiter_notes: dict[str, RecruiterNote] = Field(default_factory=dict)


class Application(CreateApplication, BaseDataModel): ...


@dataclass
class PaginatedApplications(PaginatedResponse[Application]):
    data: list[Application]


class CompanyApplicationView(Application):
    user: User | AlgoliaCandidateSearch
    resume: Resume
    job: DataReducedJob


@dataclass
class PaginatedCompanyApplicationView(PaginatedResponse[CompanyApplicationView]):
    data: list[CompanyApplicationView]


class UserApplicationView(Application):
    resume: Resume
    job: JobNameOnly
    company: DataReducedCompany


@dataclass
class PaginatedUserApplicationView(PaginatedResponse[UserApplicationView]):
    data: list[UserApplicationView]
