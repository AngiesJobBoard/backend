from enum import Enum
from pydantic import BaseModel
from ajb.contexts.companies.jobs.models import UserCreateJob


class JobWebhookEventType(str, Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    HIRED = "hired"


class CreateJobWebhook(UserCreateJob):
    external_reference_code: str


class UpdateJobWebhook(UserCreateJob):
    external_reference_code: str


class DeleteJobWebhook(BaseModel):
    external_reference_code: str


class MarkJobAsHiredWebhook(BaseModel):
    external_reference_code: str


class JobsWebhook(BaseModel):
    data: dict
    type: JobWebhookEventType
