from ajb.base import (
    Collection,
    MultipleChildrenRepository,
    RepositoryRegistry,
    RequestScope,
)

from .models import CreateCompanyNotification, CompanyNotification


class CompanyNotificationRepository(
    MultipleChildrenRepository[CreateCompanyNotification, CompanyNotification]
):
    collection = Collection.COMPANY_NOTIFICATIONS
    entity_model = CompanyNotification

    def __init__(self, request_scope: RequestScope, company_id: str | None = None):
        super().__init__(
            request_scope,
            parent_collection=Collection.COMPANIES.value,
            parent_id=company_id,
        )


RepositoryRegistry.register(CompanyNotificationRepository)
