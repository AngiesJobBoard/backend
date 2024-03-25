from datetime import datetime
from enum import Enum
from dataclasses import dataclass
from pydantic import BaseModel
from ajb.base import BaseDataModel, PaginatedResponse
from ajb.contexts.applications.enumerations import ApplicationStatus


class UpdateType(str, Enum):
    NOTE = "note"
    STATUS_CHANGE = "status_change"
    ADD_TO_SHORTLIST = "add_to_shortlist"
    REMOVE_FROM_SHORTLIST = "remove_from_shortlist"
    APPLICATION_VIEWED = "application_viewed"


class UserCreateApplicationUpdate(BaseModel):
    comment: str | None
    new_application_status: ApplicationStatus | None
    added_by_ajb_admin: bool = False


class CreateApplicationUpdate(UserCreateApplicationUpdate):
    type: UpdateType
    company_id: str
    job_id: str
    application_id: str
    recruiter_id: str


class ApplicationUpdate(CreateApplicationUpdate, BaseDataModel):
    ...


class CompanyApplicationUpdateView(UserCreateApplicationUpdate):
    email: str
    first_name: str
    last_name: str
    image_url: str | None


@dataclass
class PaginatedCompanyUpdateView(PaginatedResponse[CompanyApplicationUpdateView]):  # type: ignore
    data: list[CompanyApplicationUpdateView]


class ApplicationUpdateQuery(BaseModel):
    company_id: str
    job_id: str | None = None
    application_id: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    page: int = 0
    page_size: int = 25


class UserCreateRecruiterComment(BaseModel):
    comment: str
