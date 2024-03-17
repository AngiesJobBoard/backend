from enum import Enum
from pydantic import BaseModel

from ajb.base import BaseUseCase, Collection


class ApplicantsWebhookType(str, Enum):
    applicant_created = "applicant_created"
    applicant_updated = "applicant_updated"
    applicant_deleted = "applicant_deleted"
    applicant_hired = "applicant_hired"
    applicant_rejected = "applicant_rejected"


class ApplicantsWebookEvent(BaseModel):
    token: str
    resume_file_url: str | None = None
    event_type: ApplicantsWebhookType


class WebhookApplicantsUseCase(BaseUseCase):

    def generate_webhook_api_key(self, company_id: str, job_id: str):
        ...
    
    def handle_webhook_event(self, event: ApplicantsWebookEvent):
        ...

    def create_applicant(
        self,
    ):
        ...

    def update_applicant(
        self,
    ):
        ...
    
    def delete_applicant(
        self,
    ):
        ...

    def mark_applicant_as_hired(
        self,
    ):
        ...

    def mark_applicant_as_rejected(
        self,
    ):
        ...
