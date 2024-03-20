from ajb.base import Collection, MultipleChildrenRepository, RepositoryRegistry, RequestScope
from .models import CreateCompanyAPIEgress, CompanyAPIEgress


class CompanyAPIEgressRepository(
    MultipleChildrenRepository[CreateCompanyAPIEgress, CompanyAPIEgress]
):
    collection = Collection.COMPANY_API_EGRESS_WEBHOOKS
    entity_model = CompanyAPIEgress

    def __init__(self, request_scope: RequestScope, company_id: str | None = None):
        super().__init__(
            request_scope,
            parent_collection=Collection.COMPANIES.value,
            parent_id=company_id,
        )

RepositoryRegistry.register(CompanyAPIEgressRepository)
