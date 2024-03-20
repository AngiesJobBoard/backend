from ajb.base import (
    Collection,
    MultipleChildrenRepository,
    RepositoryRegistry,
    RequestScope,
)

from .models import CreateCompanyEmailIngress, CompanyEmailIngress


class CompanyEmailIngressRepository(
    MultipleChildrenRepository[CreateCompanyEmailIngress, CompanyEmailIngress]
):
    collection = Collection.COMPANY_EMAIL_INGRESS_WEBHOOKS
    entity_model = CompanyEmailIngress

    def __init__(self, request_scope: RequestScope, company_id: str | None = None):
        super().__init__(
            request_scope,
            parent_collection=Collection.COMPANIES.value,
            parent_id=company_id,
        )


RepositoryRegistry.register(CompanyEmailIngressRepository)
