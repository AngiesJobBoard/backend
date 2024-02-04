from pydantic import BaseModel

from ajb.contexts.companies.jobs.models import AlgoliaJobRecord
from ajb.vendor.algolia.models import AlgoliaSearchParams, AlgoliaSearchResults


class JobSearchContext(BaseModel):
    user_id: str


class SearchJobsParams(BaseModel):
    text_search: str = ""
    category: str | None = None
    company_name: str | None = None
    city: str | None = None
    schedule: str | None = None
    page: int = 0
    hits_per_page: int = 10

    def to_algolia_search(self, context: JobSearchContext) -> AlgoliaSearchParams:
        filter_dict = {}
        if self.category:
            filter_dict["category"] = self.category
        if self.company_name:
            filter_dict["company_name"] = self.company_name
        if self.city:
            filter_dict["location.city"] = self.city
        if self.schedule:
            filter_dict["schedule"] = self.schedule
        return AlgoliaSearchParams(
            query=self.text_search,
            # filters=filter_dict,
            page=self.page,
            hits_per_page=self.hits_per_page,
            user_id=context.user_id,
        )


class AlgoliaJobSearchResults(AlgoliaSearchResults):
    hits: list[AlgoliaJobRecord]

    @classmethod
    def convert_from_algolia(cls, algolia_results: AlgoliaSearchResults):
        return cls(
            hits=[
                AlgoliaJobRecord.convert_from_algolia(hit)
                for hit in algolia_results.hits
            ],
            nbHits=algolia_results.nbHits,
            page=algolia_results.page,
            nbPages=algolia_results.nbPages,
            hitsPerPage=algolia_results.hitsPerPage,
            exhaustiveNbHits=algolia_results.exhaustiveNbHits,
        )
