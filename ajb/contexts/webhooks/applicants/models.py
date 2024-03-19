from enum import Enum
from pydantic import BaseModel
from ajb.contexts.applications.models import UserCreatedApplication


class ApplicantWebhookEventType(str, Enum):
    CREATE = "create"


class CreateApplicantWebhook(UserCreatedApplication):
    external_job_reference_code: str
    external_reference_code: str


class ApplicantsWebhook(BaseModel):
    data: dict
    type: ApplicantWebhookEventType
