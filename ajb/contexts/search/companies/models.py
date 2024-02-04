from pydantic import BaseModel

from ajb.contexts.companies.models import Company, NumEmployeesEnum
from ajb.vendor.algolia.models import AlgoliaSearchParams, AlgoliaSearchResults


class CompanySearchContext(BaseModel):
    user_id: str


class CompanySearchParams(AlgoliaSearchParams):
    text_search: str = ""
    num_employees: NumEmployeesEnum | None = None
    benefits: str | None = None  # This is an array?

    def to_algolia_search(self, context: CompanySearchContext) -> AlgoliaSearchParams:
        # filter_dict = {}
        # if self.num_employees:
        #     filter_dict["num_employees"] = self.num_employees
        # if self.benefits:
        #     filter_dict["benefits"] = self.benefits
        return AlgoliaSearchParams(
            query=self.text_search,
            # filters=filter_dict,
            user_id=context.user_id,
        )


class AlgoliaCompanySearchResults(AlgoliaSearchResults):
    hits: list[Company]

    @classmethod
    def convert_from_algolia(cls, algolia_results: AlgoliaSearchResults):
        return cls(
            hits=[Company.model_validate(hit) for hit in algolia_results.hits],
            nbHits=algolia_results.nbHits,
            page=algolia_results.page,
            nbPages=algolia_results.nbPages,
            hitsPerPage=algolia_results.hitsPerPage,
            exhaustiveNbHits=algolia_results.exhaustiveNbHits,
        )
