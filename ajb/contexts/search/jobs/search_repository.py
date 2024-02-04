"""

This module handles searching for jobs ( very critical :) )

A search should take a few things:

1. Basic search params (query, filters, facet_filters, attributes_to_retrieve, page, hits_per_page)
2. User search context (user_id, prefernces, history?, etc?)

It should return search results immeidately using algolia instant search
and log all results as pages are served as impressions

If a user clicks on a result they are given the record from Algolia, where a click is then logged


Other responsibilities:

handle anonymous user searches

all search data needs to be able to be parameterized for a URL so that a search can be shared
and when logged it can be recreated through a URL

results need to be boosted based on... well many things (start simple)

 
Get all job categories

"""

from ajb.base import RequestScope
from ajb.base.events import SourceServices
from ajb.contexts.companies.jobs.models import AlgoliaJobRecord
from ajb.contexts.users.events import UserEventProducer
from ajb.vendor.algolia.models import AlgoliaSearchParams, AlgoliaFacetSearchResults
from ajb.vendor.algolia.repository import AlgoliaSearchRepository, AlgoliaIndex

from .models import SearchJobsParams, JobSearchContext, AlgoliaJobSearchResults


class JobSearchRepository:
    def __init__(
        self,
        request_scope: RequestScope,
        job_search: AlgoliaSearchRepository | None = None,
    ):
        self.request_scope = request_scope
        self.job_search = job_search or AlgoliaSearchRepository(AlgoliaIndex.JOBS)

    def search(
        self,
        context: JobSearchContext,
        query: SearchJobsParams = SearchJobsParams(),
    ) -> AlgoliaJobSearchResults:
        results = AlgoliaJobSearchResults.convert_from_algolia(
            self.job_search.search(query.to_algolia_search(context))
        )
        UserEventProducer(self.request_scope, SourceServices.API).user_views_jobs(
            results,
            query.page,
        )
        return results

    def search_job_categories(self, search: str = "*") -> AlgoliaFacetSearchResults:
        return self.job_search.search_facet(
            "category", AlgoliaSearchParams(query=search)
        )

    def get_job(self, job_id: str) -> AlgoliaJobRecord:
        record = AlgoliaJobRecord.convert_from_algolia(self.job_search.get(job_id))
        UserEventProducer(self.request_scope, SourceServices.API).user_clicks_job(
            company_id=record.company_id, job_id=record.job_id
        )
        return record
