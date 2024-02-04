from ajb.base import (
    Collection,
    MultipleChildrenRepository,
    RepositoryRegistry,
    RequestScope,
    QueryFilterParams,
    RepoFilterParams,
)
from ajb.vendor.arango.models import Filter
from .models import CreateCompanyNotification, CompanyNotification


class CompanyNotificationRepository(
    MultipleChildrenRepository[CreateCompanyNotification, CompanyNotification]
):
    collection = Collection.COMPANY_NOTIFICATIONS
    entity_model = CompanyNotification

    def __init__(self, request_scope: RequestScope, company_id: str):
        super().__init__(
            request_scope,
            parent_collection=Collection.COMPANIES.value,
            parent_id=company_id,
        )

    def get_unread_notifications(
        self, query: QueryFilterParams | RepoFilterParams = RepoFilterParams()
    ):
        if isinstance(query, QueryFilterParams):
            query = query.convert_to_repo_filters()
        query.filters.append(Filter(field="is_read", value=False))
        return self.query(query)

    def mark_as_read(self, notification_ids: list[str]) -> bool:
        self.update_many(
            {notification_id: {"is_read": True} for notification_id in notification_ids}
        )
        return True

    def mark_as_unread(self, notification_ids: list[str]) -> bool:
        self.update_many(
            {
                notification_id: {"is_read": False}
                for notification_id in notification_ids
            }
        )
        return True


RepositoryRegistry.register(CompanyNotificationRepository)
