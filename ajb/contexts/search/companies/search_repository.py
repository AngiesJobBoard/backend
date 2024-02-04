from ajb.base import RequestScope
from ajb.base.events import SourceServices
from ajb.contexts.users.events import UserEventProducer
from ajb.contexts.companies.models import Company
from ajb.vendor.algolia.repository import AlgoliaSearchRepository, AlgoliaIndex

from .models import (
    CompanySearchContext,
    CompanySearchParams,
    AlgoliaCompanySearchResults,
)


class CompanySearchRepository:
    def __init__(
        self,
        request_scope: RequestScope,
        company_search: AlgoliaSearchRepository | None = None,
    ):
        self.request_scope = request_scope
        self.company_search = company_search or AlgoliaSearchRepository(
            AlgoliaIndex.COMPANIES
        )

    def search(
        self,
        context: CompanySearchContext,
        query: CompanySearchParams = CompanySearchParams(),
    ) -> AlgoliaCompanySearchResults:
        results = AlgoliaCompanySearchResults.convert_from_algolia(
            self.company_search.search(query.to_algolia_search(context))
        )
        UserEventProducer(self.request_scope, SourceServices.API).user_views_companies(
            results,
            query.page,
        )
        return results

    def get_company(self, company_id: str) -> Company:
        record = Company.model_validate(self.company_search.get(company_id))
        UserEventProducer(self.request_scope, SourceServices.API).user_clicks_company(
            company_id=record.id
        )
        return record
