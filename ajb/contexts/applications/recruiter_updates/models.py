from datetime import datetime
from enum import Enum
from dataclasses import dataclass
from pydantic import BaseModel
from ajb.base import BaseDataModel, PaginatedResponse


class UpdateType(str, Enum):
    NOTE = "note"
    STATUS_CHANGE = "status_change"
    ADD_TO_SHORTLIST = "add_to_shortlist"
    REMOVE_FROM_SHORTLIST = "remove_from_shortlist"
    APPLICATION_VIEWED = "application_viewed"


class UserCreateApplicationUpdate(BaseModel):
    comment: str | None
    new_application_status: str | None
    added_by_ajb_admin: bool = False


class CreateApplicationUpdate(UserCreateApplicationUpdate):
    type: UpdateType
    company_id: str
    job_id: str
    application_id: str
    recruiter_id: str


class ApplicationUpdate(CreateApplicationUpdate, BaseDataModel): ...


class ApplicationUpdateRecruiterModel(BaseModel):
    first_name: str
    last_name: str
    email: str


class CompanyApplicationUpdateView(CreateApplicationUpdate, BaseDataModel):
    recruiter: ApplicationUpdateRecruiterModel


@dataclass
class PaginatedCompanyUpdateView(PaginatedResponse[CompanyApplicationUpdateView]):
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
