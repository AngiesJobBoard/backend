from ajb.base import (
    Collection,
    MultipleChildrenRepository,
    RepositoryRegistry,
    RequestScope,
)
from .models import CreateUserNotification, UserNotification


class UserNotificationRepository(
    MultipleChildrenRepository[CreateUserNotification, UserNotification]
):
    collection = Collection.USER_NOTIFICATIONS
    entity_model = UserNotification

    def __init__(self, request_scope: RequestScope, user_id: str | None = None):
        super().__init__(
            request_scope,
            parent_collection=Collection.USERS.value,
            parent_id=user_id or request_scope.user_id,
        )


RepositoryRegistry.register(UserNotificationRepository)
