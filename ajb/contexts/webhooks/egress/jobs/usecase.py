from ajb.base import Collection
from ajb.contexts.companies.api_egress_webhooks.models import (
    EgressWebhookEvent,
    EgressObjectType,
)
from ajb.contexts.companies.jobs.models import Job
from ajb.contexts.webhooks.egress.webhook_egress import BaseWebhookEgress
from ajb.vendor.mixpanel import MixpanelDomainEvents


class CompanyJobWebhookEgress(BaseWebhookEgress):
    object_type = EgressObjectType.JOB

    def send_create_job_webhook(self, company_id: str, job_id: str):
        EVENT = EgressWebhookEvent.CREATE_JOB
        all_egress_records = self.get_all_egress_records_with_event(company_id, EVENT)
        if not all_egress_records:
            return

        job: Job = self.get_object(Collection.JOBS, job_id)
        mixpanel = MixpanelDomainEvents()
        for record in all_egress_records:
            self.send_request(
                data=job.model_dump(),
                egress_record=record,
                event=EVENT,
                object_type=self.object_type,
            )
            mixpanel.job_forwarded_from_webhook(company_id, job_id)

    def send_update_job_webhook(self, company_id: str, job_id: str):
        EVENT = EgressWebhookEvent.UPDATE_JOB
        all_egress_records = self.get_all_egress_records_with_event(company_id, EVENT)
        if not all_egress_records:
            return

        job: Job = self.get_object(Collection.JOBS, job_id)
        for record in all_egress_records:
            self.send_request(
                data=job.model_dump(),
                egress_record=record,
                event=EVENT,
                object_type=self.object_type,
            )

    def send_delete_job_webhook(self, company_id: str, job_id: str):
        EVENT = EgressWebhookEvent.DELETE_JOB
        all_egress_records = self.get_all_egress_records_with_event(company_id, EVENT)
        if not all_egress_records:
            return

        for record in all_egress_records:
            self.send_request(
                data={"id": job_id},
                egress_record=record,
                event=EVENT,
                object_type=self.object_type,
            )
