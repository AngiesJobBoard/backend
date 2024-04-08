from dataclasses import dataclass
from pydantic import BaseModel
from ajb.base import BaseDataModel, PaginatedResponse
from ajb.contexts.users.models import User

from ..models import RecruiterRole


class UserCreateRecruiter(BaseModel):
    role: RecruiterRole
    user_id: str
    company_id: str


class RecruiterNotificationSettings(BaseModel):
    send_daily_updates: bool | None = None
    send_weekly_updates: bool | None = None
    send_high_match_application_updates: bool | None = None
    send_interesting_application_updates: bool | None = None


class UserUpdateRecruiter(BaseModel):
    settings: RecruiterNotificationSettings = RecruiterNotificationSettings()


class CreateRecruiter(UserCreateRecruiter, UserUpdateRecruiter): ...


class Recruiter(CreateRecruiter, BaseDataModel): ...


class RecruiterAndUser(Recruiter):
    user: User


@dataclass
class PaginatedRecruiterAndUser(PaginatedResponse[RecruiterAndUser]):
    data: list[RecruiterAndUser]


class CompanyAndRole(BaseModel):
    role: RecruiterRole
    company_id: str
