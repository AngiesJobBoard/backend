from ajb.base import (
    ParentRepository,
    RepositoryRegistry,
    Collection,
    QueryFilterParams,
    RepoFilterParams,
)
from ajb.vendor.arango.models import Join

from .models import AdminUser, CreateAdminUser, AdminAndUser


class AdminUserRepository(ParentRepository[CreateAdminUser, AdminUser]):
    collection = Collection.ADMIN_USERS
    entity_model = AdminUser

    def get_admin_and_user(
        self, query: QueryFilterParams | RepoFilterParams = RepoFilterParams()
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


RepositoryRegistry.register(AdminUserRepository)
