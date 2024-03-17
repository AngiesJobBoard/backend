from pydantic import BaseModel

from ajb.base import BaseUseCase, Collection



class JobsWebhookEvent(BaseModel):
    company_id: str


class WebhookJobsUseCase(BaseUseCase):
    
    def handle_webhook_event(self, event: JobsWebhookEvent):
        ...

    def create_job(
        self,
    ):
        ...

    def update_job(
        self,
    ):
        ...
    
    def delete_job(
        self,
    ):
        ...

    def mark_job_as_hired(
        self,
    ):
        ...
