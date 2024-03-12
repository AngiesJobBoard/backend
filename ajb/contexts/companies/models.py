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


class UpdateCompany(BaseModel):
    name: str | None = None
    num_employees: NumEmployeesEnum | None = None


class CreateCompany(UserCreateCompany):
    created_by_user: str
    owner_email: str
    total_jobs: int = 0
    total_applicants: int = 0
    shortlisted_applicants: int = 0
    high_matching_applicants: int = 0
    new_applicants: int = 0


class Company(BaseDataModel, CreateCompany): ...


@dataclass
class CompanyPaginatedResponse(PaginatedResponse[Company]):
    data: list[Company]


class RecruiterRole(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
