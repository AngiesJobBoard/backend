from dataclasses import dataclass
from pydantic import BaseModel, Field

from ajb.base import BaseDataModel, PaginatedResponse
from ajb.base.events import CompanyEvent, UserEvent


class CreateCompanyNotification(BaseModel):
    company_id: str
    notification_type: CompanyEvent | UserEvent
    title: str
    message: str
    candidate_id: str | None = None
    job_id: str | None = None
    metadata: dict = Field(default_factory=dict)
    is_read: bool = False


class CompanyNotification(CreateCompanyNotification, BaseDataModel): ...


@dataclass
class PaginatedCompanyNotifications(PaginatedResponse[CompanyNotification]):
    data: list[CompanyNotification]
