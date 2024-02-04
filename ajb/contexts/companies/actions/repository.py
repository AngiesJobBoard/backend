from ajb.base import (
    ParentRepository,
    RepositoryRegistry,
    Collection,
    QueryFilterParams,
    RepoFilterParams,
)
from ajb.base.events import CompanyEvent
from ajb.vendor.arango.models import Filter

from .models import CreateCompanyAction, CompanyAction


class CompanyActionRepository(ParentRepository[CreateCompanyAction, CompanyAction]):
    collection = Collection.COMPANY_ACTIONS
    entity_model = CompanyAction

    def query_event_type(
        self,
        company_id: str | None = None,
        event: CompanyEvent | None = None,
        query: QueryFilterParams | RepoFilterParams = RepoFilterParams(),
    ):
        if isinstance(query, QueryFilterParams):
            query = query.convert_to_repo_filters()
        if company_id:
            query.filters.append(Filter(field="company_id", value=company_id))
        if event:
            query.filters.append(Filter(field="action", value=event.value))
        return self.query(query)


RepositoryRegistry.register(CompanyActionRepository)
