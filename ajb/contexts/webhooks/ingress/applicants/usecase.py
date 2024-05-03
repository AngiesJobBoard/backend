from datetime import datetime
from ajb.base import BaseUseCase, Collection
from ajb.contexts.applications.usecase import ApplicationUseCase
from ajb.contexts.applications.models import CreateApplication
from ajb.contexts.companies.jobs.models import Job
from ajb.contexts.companies.api_ingress_webhooks.models import (
    CompanyAPIIngress,
    UpdateIngress,
)
from ajb.contexts.companies.api_ingress_webhooks.repository import (
    CompanyAPIIngressRepository,
)
from ajb.contexts.webhooks.ingress.applicants.application_raw_storage.repository import (
    CreateRawIngressApplication,
    RawIngressApplicationRepository,
)
from .models import CreateApplicantWebhook


class WebhookApplicantsUseCase(BaseUseCase):

    def handle_webhook_event(self, ingress_record: CompanyAPIIngress, event: dict):
        CompanyAPIIngressRepository(
            self.request_scope, ingress_record.company_id
        ).update(
            id=ingress_record.id,
            data=UpdateIngress(
                last_message_received=datetime.now(),
                last_message=event,
            ),
            merge=False,
        )
        RawIngressApplicationRepository(self.request_scope).create(
            CreateRawIngressApplication(
                company_id=ingress_record.company_id,
                application_id="still_testing",
                ingress_id=ingress_record.id,
                data=event,
            )
        )

    def create_applicant(self, company_id: str, data: CreateApplicantWebhook):
        job_repo = self.get_repository(Collection.JOBS, self.request_scope, company_id)
        job: Job = job_repo.get_one(
            company_id=company_id, external_reference_code=data.external_reference_code
        )
        return ApplicationUseCase(self.request_scope).create_application(
            company_id,
            data.external_job_reference_code,
            CreateApplication(
                **data.model_dump(), company_id=company_id, job_id=job.id
            ),
            True,
        )
