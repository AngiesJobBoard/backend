from dataclasses import dataclass
from pydantic import BaseModel
from ajb.base import BaseDataModel, PaginatedResponse
from ajb.contexts.users.models import User

from ..models import RecruiterRole


class UserCreateRecruiter(BaseModel):
    role: RecruiterRole
    user_id: str
    company_id: str


class CreateRecruiter(UserCreateRecruiter):
    send_daily_updates: bool = True
    send_weekly_updates: bool = True
    send_new_application_updates: bool = True
    send_email_message_updates: bool = True


class Recruiter(CreateRecruiter, BaseDataModel): ...


class RecruiterAndUser(Recruiter):
    user: User


@dataclass
class PaginatedRecruiterAndUser(PaginatedResponse[RecruiterAndUser]):
    data: list[RecruiterAndUser]


class CompanyAndRole(BaseModel):
    role: RecruiterRole
    company_id: str
