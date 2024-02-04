from ajb.base import (
    MultipleChildrenRepository,
    RequestScope,
    Collection,
    RepositoryRegistry,
    QueryFilterParams,
    RepoFilterParams,
)
from ajb.base.events import SourceServices
from ajb.vendor.arango.models import Join
from ajb.contexts.users.events import UserEventProducer
from .models import SavedCompany, CreateSavedCompany, SavedCompaniesListObject


class UserSavedCompaniesRepository(
    MultipleChildrenRepository[CreateSavedCompany, SavedCompany]
):
    collection = Collection.USER_SAVED_COMPANIES
    entity_model = SavedCompany

    def __init__(self, request_scope: RequestScope, user_id: str | None = None):
        super().__init__(
            request_scope,
            parent_collection=Collection.USERS.value,
            parent_id=user_id or request_scope.user_id,
        )

    def create(self, entity: CreateSavedCompany) -> SavedCompany:  # type: ignore
        response = super().create(entity)
        UserEventProducer(self.request_scope, SourceServices.API).user_saves_company(
            company_id=entity.company_id,
        )
        return response

    def query_with_companies(
        self, query: QueryFilterParams | RepoFilterParams = RepoFilterParams()
    ):
        return self.query_with_joins(
            joins=[
                Join(
                    to_collection_alias="company",
                    to_collection="companies",
                    from_collection_join_attr="company_id",
                ),
            ],
            repo_filters=query,
            return_model=SavedCompaniesListObject,
        )


RepositoryRegistry.register(UserSavedCompaniesRepository)
