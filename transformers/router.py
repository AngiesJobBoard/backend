"""
This is responsible for looking at a raw ingress record and routing it to the correct tranformer class
"""

from ajb.base import RequestScope
from ajb.contexts.applications.events import IngressEvent
from ajb.contexts.companies.api_ingress_webhooks.repository import (
    CompanyAPIIngressRepository,
)
from ajb.contexts.companies.api_ingress_webhooks.models import IngressSourceType
from ajb.contexts.webhooks.ingress.applicants.application_raw_storage.repository import (
    RawIngressApplicationRepository,
)

from transformers.incoming.postcardmania import IncomingPostCardManiaTransformer


TRANSFORMER_ROUTER = {
    IngressSourceType.COMPANY_WEBSITE: {
        "PostCardMania Website": IncomingPostCardManiaTransformer
    }
}


def route_transformer_request(request_scope: RequestScope, event: IngressEvent):
    ingress_record = CompanyAPIIngressRepository(request_scope, event.company_id).get(
        event.ingress_id
    )
    raw_record = RawIngressApplicationRepository(request_scope).get(
        event.raw_ingress_data_id
    )
    transformer_class = TRANSFORMER_ROUTER[ingress_record.source_type][
        ingress_record.source
    ]
    transformer_class(request_scope, raw_record).run()
