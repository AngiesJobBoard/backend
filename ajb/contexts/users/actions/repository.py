from ajb.base import (
    ParentRepository,
    RepositoryRegistry,
    Collection,
    QueryFilterParams,
    RepoFilterParams,
)
from ajb.base.events import UserEvent
from ajb.vendor.arango.models import Filter

from .models import CreateUserAction, UserAction


class UserActionRepository(ParentRepository[CreateUserAction, UserAction]):
    collection = Collection.USER_ACTIONS
    entity_model = UserAction

    def query_event_type(
        self,
        user_id: str | None = None,
        event: UserEvent | None = None,
        query: QueryFilterParams | RepoFilterParams = RepoFilterParams(),
    ):
        if isinstance(query, QueryFilterParams):
            query = query.convert_to_repo_filters()
        if user_id:
            query.filters.append(Filter(field="user_id", value=user_id))
        if event:
            query.filters.append(Filter(field="action", value=event.value))
        return self.query(query)


RepositoryRegistry.register(UserActionRepository)
