from ajb.base import BaseUseCase, Collection
from ajb.contexts.companies.jobs.usecase import JobsUseCase
from ajb.contexts.companies.jobs.models import UserCreateJob, Job
from .models import (
    JobsWebhook,
    JobWebhookEventType,
    CreateJobWebhook,
    UpdateJobWebhook,
    DeleteJobWebhook,
    MarkJobAsHiredWebhook
)


class WebhookJobsUseCase(BaseUseCase):
    
    def handle_webhook_event(self, company_id: str, event: JobsWebhook):
        if event.type == JobWebhookEventType.CREATE:
            return self.create_job(company_id, CreateJobWebhook(**event.data))
        elif event.type == JobWebhookEventType.UPDATE:
            return self.update_job(company_id, UpdateJobWebhook(**event.data))
        elif event.type == JobWebhookEventType.DELETE:
            return self.delete_job(company_id, DeleteJobWebhook(**event.data))
        elif event.type == JobWebhookEventType.HIRED:
            return self.mark_job_as_hired(company_id, MarkJobAsHiredWebhook(**event.data))
        
        raise NotImplementedError(f"Event type {event.type} is not yet supported")

    def create_job(
        self,
        company_id: str,
        data: CreateJobWebhook
    ):
        JobsUseCase(self.request_scope).create_job(company_id, data)

    def update_job(
        self,
        company_id: str,
        data: UpdateJobWebhook
    ):
        repo = self.get_repository(Collection.JOBS, self.request_scope, company_id)
        job: Job = repo.get_one(
            company_id=company_id,
            external_reference_code=data.external_reference_code
        )
        repo.update(
            job.id,
            UserCreateJob(**data.model_dump(exclude={"job_id"}))
        )
    
    def delete_job(
        self,
        company_id: str,
        data: DeleteJobWebhook
    ):
        repo = self.get_repository(Collection.JOBS, self.request_scope, company_id)
        job: Job = repo.get_one(
            company_id=company_id,
            external_reference_code=data.external_reference_code
        )
        repo.delete(job.id)

    def mark_job_as_hired(
        self,
        company_id: str,
        data: MarkJobAsHiredWebhook
    ):
        repo = self.get_repository(Collection.JOBS, self.request_scope, company_id)
        job: Job = repo.get_one(
            company_id=company_id,
            external_reference_code=data.external_reference_code
        )
        repo.update_fields(
            job.id,
            position_filled=True
        )
