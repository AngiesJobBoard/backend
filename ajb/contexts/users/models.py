from datetime import datetime
from dataclasses import dataclass
from pydantic import BaseModel

from ajb.base.models import BaseDataModel, PaginatedResponse


class UpdateUser(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    image_url: str | None = None
    phone_number: str | None = None
    show_first_time_experience: bool = True
    date_accepted_terms_of_service: datetime | None = (
        None  # IF none they have not yet accepted...
    )


class CreateUser(UpdateUser):
    first_name: str  # type: ignore
    last_name: str  # type: ignore
    email: str
    image_url: str | None = None
    phone_number: str | None = None
    auth_id: str
    profile_is_public: bool = False
    candidate_score: float | None = None
    currentSelectedCompanyId: str | None = None


class User(CreateUser, BaseDataModel): ...


@dataclass
class PaginatedUsers(PaginatedResponse[User]):
    data: list[User]


class UserProfileUpload(BaseModel):
    file_type: str
    file_name: str
    profile_picture_data: bytes
    user_id: str
