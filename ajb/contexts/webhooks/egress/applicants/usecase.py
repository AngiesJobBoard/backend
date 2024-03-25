from ajb.base import Collection
from ajb.contexts.companies.api_egress_webhooks.models import (
    EgressWebhookEvent,
    EgressObjectType,
)
from ajb.contexts.applications.models import Application
from ajb.contexts.webhooks.egress.webhook_egress import BaseWebhookEgress
from ajb.vendor.mixpanel import MixpanelDomainEvents


class CompanyApplicantsWebhookEgress(BaseWebhookEgress):
    object_type = EgressObjectType.APPLICANT

    def send_create_applicant_webhook(self, company_id: str, application_id: str):
        EVENT = EgressWebhookEvent.CREATE_APPLICANT
        all_egress_records = self.get_all_egress_records_with_event(company_id, EVENT)
        if not all_egress_records:
            return

        application: Application = self.get_object(
            Collection.APPLICATIONS, application_id
        )
        mixpanel = MixpanelDomainEvents()
        for record in all_egress_records:
            self.send_request(
                data=application.model_dump(),
                egress_record=record,
                event=EVENT,
                object_type=self.object_type,
            )
            mixpanel.application_forwarded_from_webhook(
                company_id, application.job_id, application_id
            )

    def send_update_applicant_webhook(self, company_id: str, application_id: str):
        EVENT = EgressWebhookEvent.UPDATE_APPLICANT
        all_egress_records = self.get_all_egress_records_with_event(company_id, EVENT)
        if not all_egress_records:
            return

        application: Application = self.get_object(
            Collection.APPLICATIONS, application_id
        )
        for record in all_egress_records:
            self.send_request(
                data=application.model_dump(),
                egress_record=record,
                event=EVENT,
                object_type=self.object_type,
            )

    def send_delete_applicant_webhook(self, company_id: str, application_id: str):
        EVENT = EgressWebhookEvent.DELETE_APPLICANT
        all_egress_records = self.get_all_egress_records_with_event(company_id, EVENT)
        if not all_egress_records:
            return

        for record in all_egress_records:
            self.send_request(
                data={"id": application_id},
                egress_record=record,
                event=EVENT,
                object_type=self.object_type,
            )
