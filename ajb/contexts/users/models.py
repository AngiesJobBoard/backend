from pydantic import BaseModel

from ajb.base.models import BaseDataModel


class UpdateUser(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    image_url: str | None = None
    phone_number: str | None = None
    show_first_time_experience: bool = True


class CreateUser(UpdateUser):
    first_name: str
    last_name: str
    email: str
    image_url: str | None = None
    phone_number: str | None = None
    auth_id: str
    profile_is_public: bool = False
    candidate_score: float | None = None


class User(CreateUser, BaseDataModel): ...
