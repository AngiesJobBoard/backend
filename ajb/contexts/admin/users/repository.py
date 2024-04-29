from cachetools import TTLCache, cached
from ajb.base import (
    ParentRepository,
    RepositoryRegistry,
    Collection,
    QueryFilterParams,
    RepoFilterParams,
)
from ajb.vendor.arango.models import Join

from .models import AdminUser, CreateAdminUser, AdminAndUser


ADMIN_USER_CACHE: TTLCache[str, AdminUser] = TTLCache(maxsize=1024, ttl=300)


class AdminUserRepository(ParentRepository[CreateAdminUser, AdminUser]):
    collection = Collection.ADMIN_USERS
    entity_model = AdminUser

    def get_admin_and_user(
        self, query: QueryFilterParams | RepoFilterParams | None = None
    ):
        return self.query_with_joins(
            joins=[
                Join(
                    to_collection_alias="user",
                    to_collection=Collection.USERS,
                    from_collection_join_attr="user_id",
                )
            ],
            repo_filters=query,
            return_model=AdminAndUser,
        )

    @cached(cache=ADMIN_USER_CACHE)
    def get_admin_user_by_auth_id(self, auth_id: str):
        return self.get_one(user_id=auth_id)


RepositoryRegistry.register(AdminUserRepository)
