from ajb.base import RequestScope
from ajb.base.events import SourceServices
from ajb.contexts.companies.events import CompanyEventProducer
from ajb.contexts.users.models import AlgoliaCandidateSearch
from ajb.vendor.algolia.repository import AlgoliaSearchRepository, AlgoliaIndex

from .models import (
    CandidateSearchContext,
    CandidateSearchParams,
    AlgoliaCandidateSearchResults,
)


class CandidateSearchRepository:
    def __init__(
        self,
        request_scope: RequestScope,
        candidate_search: AlgoliaSearchRepository | None = None,
    ):
        self.request_scope = request_scope
        self.candidate_search = candidate_search or AlgoliaSearchRepository(
            AlgoliaIndex.CANDIDATES
        )

    def search(
        self,
        context: CandidateSearchContext,
        query: CandidateSearchParams = CandidateSearchParams(),
    ) -> AlgoliaCandidateSearchResults:
        results = AlgoliaCandidateSearchResults.convert_from_algolia(
            self.candidate_search.search(query.to_algolia_search(context))
        )
        CompanyEventProducer(
            self.request_scope, SourceServices.API
        ).company_views_candidates(
            results,
            query.page,
        )
        return results

    def get_candidate(self, candidate_id: str) -> AlgoliaCandidateSearch:
        record = AlgoliaCandidateSearch.model_validate(
            self.candidate_search.get(candidate_id)
        )
        CompanyEventProducer(
            self.request_scope, SourceServices.API
        ).company_clicks_candidate(candidate_id=candidate_id)
        return record
