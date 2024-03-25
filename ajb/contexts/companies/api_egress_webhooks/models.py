from enum import Enum
from dataclasses import dataclass
from pydantic import BaseModel
from ajb.base import BaseDataModel, PaginatedResponse


class EgressObjectType(str, Enum):
    APPLICANT = "applicant"
    JOB = "job"


class EgressWebhookEvent(str, Enum):
    CREATE_JOB = "create_job"
    UPDATE_JOB = "update_job"
    DELETE_JOB = "delete_job"

    CREATE_APPLICANT = "create_applicant"
    UPDATE_APPLICANT = "update_applicant"
    DELETE_APPLICANT = "delete_applicant"


class WebhookEgressMessage(BaseModel):
    event: EgressWebhookEvent
    object: EgressObjectType
    data: dict


class UserCreateCompanyAPIEgress(BaseModel):
    webhook_url: str
    headers: dict[str, str]
    enabled_events: list[EgressWebhookEvent]
    is_active: bool


class CreateCompanyAPIEgress(UserCreateCompanyAPIEgress):
    company_id: str


class UpdateCompanyAPIEgress(BaseModel):
    webhook_url: str | None = None
    headers: dict[str, str] | None = None
    enabled_events: list[EgressWebhookEvent] | None = None
    is_active: bool | None = None


class CompanyAPIEgress(CreateCompanyAPIEgress, BaseDataModel): ...


@dataclass
class PaginatedCompanyEgressWebhooks(PaginatedResponse[CompanyAPIEgress]):
    data: list[CompanyAPIEgress]
