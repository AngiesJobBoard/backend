from enum import Enum
from dataclasses import dataclass
from pydantic import BaseModel

from ajb.base.models import BaseDataModel, PaginatedResponse
from ajb.common.models import DataReducedCompany, DataReducedJob

from .enumerations import NumEmployeesEnum


class UserCreateCompany(BaseModel):
    name: str
    slug: str | None = None
    num_employees: NumEmployeesEnum | None = None
    owner_first_and_last_name: str | None = None
    company_phone_number: str | None = None
    company_description: str | None = None
    company_website_link: str | None = None
    why_candidates_should_work_here: str | None = None
    main_image: str | None = None
    icon_image: str | None = None
    additional_image_urls: list[str] | None = None


class UpdateCompany(BaseModel):
    name: str | None = None
    num_employees: NumEmployeesEnum | None = None
    owner_first_and_last_name: str | None = None
    owner_email: str | None = None
    company_phone_number: str | None = None
    company_description: str | None = None
    company_website_link: str | None = None
    why_candidates_should_work_here: str | None = None
    main_image: str | None = None
    icon_image: str | None = None
    additional_image_urls: list[str] | None = None


class CreateCompany(UserCreateCompany):
    created_by_user: str
    owner_email: str


class Company(BaseDataModel, CreateCompany):
    ...


@dataclass
class CompanyPaginatedResponse(PaginatedResponse[Company]):
    data: list[Company]


class RecruiterRole(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
