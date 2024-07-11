from typing import cast
import requests

from ajb.base import BaseUseCase, Collection
from ajb.contexts.companies.api_egress_webhooks.models import (
    CompanyAPIEgress,
    EgressWebhookEvent,
    EgressObjectType,
    WebhookEgressMessage,
)


class BaseWebhookEgress(BaseUseCase):
    # AJBTODO add transformations for data?

    def get_all_egress_records_with_event(
        self, company_id: str, event: EgressWebhookEvent
    ) -> list[CompanyAPIEgress]:
        egress_repo = self.get_repository(
            Collection.COMPANY_API_EGRESS_WEBHOOKS, self.request_scope, company_id
        )
        all_egress_records, _ = egress_repo.query(is_active=True, company_id=company_id)
        if not all_egress_records:
            return []

        all_egress_records = cast(list[CompanyAPIEgress], all_egress_records)
        return [
            record for record in all_egress_records if event in record.enabled_events
        ]

    def send_request(
        self,
        *,
        data: dict,
        egress_record: CompanyAPIEgress,
        event: EgressWebhookEvent,
        object_type: EgressObjectType,
    ):
        requests.post(
            url=egress_record.webhook_url,
            headers={"Content-Type": "application/json", **egress_record.headers},
            json=WebhookEgressMessage(
                event=event, object=object_type, data=data
            ).model_dump(mode="json"),
        )
