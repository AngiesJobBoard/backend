from dataclasses import dataclass
from pydantic import BaseModel

from ajb.base.models import BaseDataModel, PaginatedResponse
from ajb.common.models import Location


class UserCreateOffice(BaseModel):
    location: Location
    name: str
    default_job_location: bool = False


class UserUpdateOffice(BaseModel):
    location: Location | None = None
    name: str | None = None
    default_job_location: bool | None = None


class CreateOffice(UserCreateOffice):
    company_id: str


class Office(BaseDataModel, CreateOffice): ...


@dataclass
class PaginatedOffice(PaginatedResponse):
    data: list[Office]
