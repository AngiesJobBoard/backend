from enum import Enum
from dataclasses import dataclass
from pydantic import BaseModel, Field

from ajb.base.models import BaseDataModel, PaginatedResponse
from ajb.common.models import Location

from .enumerations import NumEmployeesEnum


class UserCreateCompany(BaseModel):
    name: str
    slug: str | None = None
    website: str | None = None
    num_employees: NumEmployeesEnum | None = None


class ApplicationStatusRepresents(str, Enum):
    NEW = "New"
    IN_REVIEW = "In Review"
    INTERESTED = "Interested"
    HIRED = "Hired"
    REJECTED = "Rejected"


class ApplicationStatuses(BaseModel):
    label: str
    represents: ApplicationStatusRepresents


def default_statuses():
    return [
        ApplicationStatuses(
            label="To Review", represents=ApplicationStatusRepresents.NEW
        ),
        ApplicationStatuses(
            label="Left Voicemail", represents=ApplicationStatusRepresents.IN_REVIEW
        ),
        ApplicationStatuses(
            label="Emailed", represents=ApplicationStatusRepresents.IN_REVIEW
        ),
        ApplicationStatuses(
            label="Phone Interview", represents=ApplicationStatusRepresents.INTERESTED
        ),
        ApplicationStatuses(
            label="In Person Interview",
            represents=ApplicationStatusRepresents.INTERESTED,
        ),
        ApplicationStatuses(
            label="Declined", represents=ApplicationStatusRepresents.REJECTED
        ),
        ApplicationStatuses(
            label="Hired", represents=ApplicationStatusRepresents.HIRED
        ),
    ]


class CompanySettings(BaseModel):
    enable_all_email_ingress: bool = False
    enable_job_api_ingress: bool = False
    enable_applicant_api_ingress: bool = False
    application_statuses: list[ApplicationStatuses] = Field(
        default_factory=default_statuses
    )
    default_location: Location | None = None


class UpdateCompany(BaseModel):
    name: str | None = None
    num_employees: NumEmployeesEnum | None = None
    owner_email: str | None = None
    settings: CompanySettings | None = None
    company_has_created_first_job: bool | None = None
    company_has_imported_first_application: bool | None = None
    main_image: str | None = None
    icon_image: str | None = None


class CreateCompany(UserCreateCompany):
    created_by_user: str
    owner_email: str
    settings: CompanySettings = CompanySettings()
    total_jobs: int = 0
    total_applicants: int = 0
    high_matching_applicants: int = 0
    new_applicants: int = 0
    company_has_created_first_job: bool = False
    company_has_imported_first_application: bool = False
    stripe_customer_id: str | None = None
    main_image: str | None = None
    icon_image: str | None = None


class Company(BaseDataModel, CreateCompany): ...


@dataclass
class CompanyPaginatedResponse(PaginatedResponse[Company]):
    data: list[Company]


class RecruiterRole(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"


class CompanyNameAndID(BaseDataModel):
    name: str


class CompanyGlobalSearchJobs(BaseDataModel):
    position_title: str
    total_applicants: int


class CompanyGlobalSearchApplications(BaseDataModel):
    name: str
    email: str
    phone: str
    job: CompanyGlobalSearchJobs


class CompanyGlobalSearchResults(BaseModel):
    jobs: list[CompanyGlobalSearchJobs]
    applications: list[CompanyGlobalSearchApplications]


class CompanyImageUpload(BaseModel):
    file_type: str
    file_name: str
    picture_data: bytes
