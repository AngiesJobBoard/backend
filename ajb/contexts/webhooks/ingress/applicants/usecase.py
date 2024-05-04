from datetime import datetime
from ajb.base import BaseUseCase
from ajb.base.events import SourceServices
from ajb.contexts.companies.api_ingress_webhooks.models import (
    CompanyAPIIngress,
    UpdateIngress,
)
from ajb.contexts.companies.api_ingress_webhooks.repository import (
    CompanyAPIIngressRepository,
)
from ajb.contexts.webhooks.ingress.applicants.application_raw_storage.repository import (
    CreateRawIngressApplication,
    RawIngressApplication,
    RawIngressApplicationRepository,
)
from ajb.contexts.applications.events import ApplicationEventProducer


class WebhookApplicantsUseCase(BaseUseCase):

    def _update_ingress_record_time(self, ingress_record: CompanyAPIIngress):
        CompanyAPIIngressRepository(
            self.request_scope, ingress_record.company_id
        ).update(
            id=ingress_record.id,
            data=UpdateIngress(
                last_message_received=datetime.now(),
            ),
            merge=False,
        )

    def _store_raw_ingress_data(self, ingress_record: CompanyAPIIngress, event: dict):
        return RawIngressApplicationRepository(self.request_scope).create(
            CreateRawIngressApplication(
                company_id=ingress_record.company_id,
                ingress_id=ingress_record.id,
                data=event,
            )
        )

    def _produce_ingress_event(
        self,
        ingress_record: CompanyAPIIngress,
        created_raw_record: RawIngressApplication,
    ):
        ApplicationEventProducer(
            self.request_scope, SourceServices.WEBHOOK
        ).ingress_event(
            company_id=ingress_record.company_id,
            ingress_id=ingress_record.id,
            raw_ingress_data_id=created_raw_record.id,
        )

    def handle_webhook_event(self, ingress_record: CompanyAPIIngress, event: dict):
        self._update_ingress_record_time(ingress_record)
        created_raw_record = self._store_raw_ingress_data(ingress_record, event)
        self._produce_ingress_event(ingress_record, created_raw_record)
