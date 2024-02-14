from dataclasses import dataclass
from pydantic import BaseModel, Field


from ajb.base import BaseDataModel, PaginatedResponse
from ajb.base.events import UserEvent, CompanyEvent


class CreateUserNotification(BaseModel):
    user_id: str
    notification_type: UserEvent | CompanyEvent
    title: str
    message: str
    company_id: str | None = None
    job_id: str | None = None
    metadata: dict = Field(default_factory=dict)
    is_read: bool = False


class UserNotification(CreateUserNotification, BaseDataModel):
    ...


@dataclass
class PaginatedUserNotifications(PaginatedResponse[UserNotification]):
    data: list[UserNotification]
