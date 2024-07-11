from ajb.base import Collection, MultipleChildrenRepository, RepositoryRegistry

from .models import CreateAuditEvent, AuditEvent


class BillingAuditEventsRepository(
    MultipleChildrenRepository[CreateAuditEvent, AuditEvent]
):
    collection = Collection.BILLING_AUDIT_EVENTS
    entity_model = AuditEvent

    def __init__(self, request_scope, company_id: str):
        super().__init__(request_scope, Collection.COMPANIES, company_id)
        self.company_id = company_id


RepositoryRegistry.register(BillingAuditEventsRepository)
