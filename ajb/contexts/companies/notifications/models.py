from enum import Enum
from dataclasses import dataclass
from pydantic import BaseModel, Field

from ajb.base import BaseDataModel, PaginatedResponse


class NotificationType(str, Enum):
    HIGH_MATCHING_CANDIDATE = "high_matching_candidate"
    APPLICATION_STATUS_CHANGE = "application_status_change"


class SystemCreateCompanyNotification(BaseModel):
    company_id: str
    notification_type: NotificationType
    title: str
    message: str
    application_id: str | None = None
    job_id: str | None = None
    metadata: dict = Field(default_factory=dict)


class CreateCompanyNotification(SystemCreateCompanyNotification):
    recruiter_id: str
    is_read: bool = False


class CompanyNotification(CreateCompanyNotification, BaseDataModel): ...


@dataclass
class PaginatedCompanyNotifications(PaginatedResponse[CompanyNotification]):
    data: list[CompanyNotification]
