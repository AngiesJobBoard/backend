from ajb.base import (
    MultipleChildrenRepository,
    Collection,
    RepositoryRegistry,
    QueryFilterParams,
    RequestScope,
    RepoFilterParams,
)
from ajb.vendor.arango.models import Join, Filter
from ajb.exceptions import GenericTypeError

from .models import Recruiter, CreateRecruiter, RecruiterAndUser, CompanyAndRole


class RecruiterRepository(MultipleChildrenRepository[CreateRecruiter, Recruiter]):
    collection = Collection.COMPANY_RECRUITERS
    entity_model = Recruiter

    def __init__(self, request_scope: RequestScope, company_id: str | None = None):
        super().__init__(
            request_scope,
            parent_collection=Collection.COMPANIES.value,
            parent_id=company_id,
        )

    def get_recruiters_by_company(
        self, company_id: str, query: QueryFilterParams = QueryFilterParams()
    ) -> tuple[list[RecruiterAndUser], int]:
        filter_params = query.convert_to_repo_filters()
        filter_params.filters.append(Filter(field="company_id", value=company_id))
        return self.query_with_joins(  # type: ignore
            joins=[
                Join(
                    to_collection_alias="user",
                    to_collection="users",
                    from_collection_join_attr="user_id",
                )
            ],
            repo_filters=filter_params,
            return_model=RecruiterAndUser,
        )

    def get_recruiter_by_id(self, recruiter_id: str) -> RecruiterAndUser:
        results = self.get_with_joins(
            id=recruiter_id,
            joins=[
                Join(
                    to_collection_alias="user",
                    to_collection="users",
                    from_collection_join_attr="user_id",
                )
            ],
            return_model=RecruiterAndUser,
        )
        if isinstance(results, RecruiterAndUser):
            return results
        raise GenericTypeError(f"Expected RecruiterAndUser, got {type(results)}")

    def get_companies_by_user_id(self, user_id: str) -> list[CompanyAndRole]:
        results, _ = self.query(
            repo_filters=RepoFilterParams(
                filters=[Filter(field="user_id", value=user_id)]
            )
        )
        return [CompanyAndRole(**result.model_dump()) for result in results]


RepositoryRegistry.register(RecruiterRepository)
