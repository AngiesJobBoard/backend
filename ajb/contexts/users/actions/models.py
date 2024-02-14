import typing as t
from dataclasses import dataclass
from pydantic import Field

from ajb.base import BaseAction, BaseDataModel, PaginatedResponse
from ajb.base.events import UserEvent


class CreateUserAction(BaseAction):
    action: UserEvent
    user_is_anonymous: bool
    job_id: str | None = None
    company_id: str | None = None
    application_id: str | None = None
    position: int | None = None
    metadata: dict[str, t.Any] = Field(default_factory=dict)


class UserAction(BaseDataModel, CreateUserAction):
    ...


@dataclass
class PaginatedUserActions(PaginatedResponse[UserAction]):
    data: list[UserAction]
