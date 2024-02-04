import typing as t
from enum import Enum
from pydantic import BaseModel


class AlgoliaIndex(str, Enum):
    JOBS = "job_search"
    COMPANIES = "company_search"
    CANDIDATES = "candidate_search"


class AlgoliaSearchOperators(str, Enum):
    EQUALS = "="
    NOT_EQUALS = "!="
    LESS_THAN = "<"
    LESS_THAN_OR_EQUAL = "<="
    GREATER_THAN = ">"
    GREATER_THAN_OR_EQUAL = ">="
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"


class AlgoliaSearchParams(BaseModel):
    query: str = "*"
    user_id: str | None = None
    # filters: dict[str, t.Any] = Field(default_factory=dict)
    # facet_filters: dict[str, t.Any] = Field(default_factory=dict)
    attributes_to_retrieve: str | None = None
    page: int = 0
    hits_per_page: int = 10

    def convert_to_request_options(self):
        output = {}
        # if self.filters:
        #     output["filters"] = []
        # for key, value in self.filters.items():
        #     output["filters"].append(f"{key}:{value}")
        # if self.facet_filters:
        #     output["facetFilters"] = []
        # for key, value in self.facet_filters.items():
        # output["facetFilters"].append(f"{key}:{value}")
        if self.attributes_to_retrieve:
            output["attributesToRetrieve"] = self.attributes_to_retrieve
        if self.page:
            output["page"] = self.page
        if self.hits_per_page:
            output["hitsPerPage"] = self.hits_per_page
        if self.user_id:
            output["userToken"] = self.user_id
        return output


class AlgoliaSearchResults(BaseModel):
    hits: list[t.Any]
    nbHits: int
    page: int
    nbPages: int
    hitsPerPage: int
    exhaustiveNbHits: bool


class AlgoliaFacetHit(BaseModel):
    value: str
    highlighted: str
    count: int


class AlgoliaFacetSearchResults(BaseModel):
    facetHits: list[AlgoliaFacetHit]


class InsightsAction(str, Enum):
    VIEW = "view"
    CLICK = "click"
    CONVERSION = "conversion"


class InsightsEvent(BaseModel):
    eventType: InsightsAction
    eventName: str
    userToken: str | None
    objectIDs: list[str]
    positions: list[int] | None = None  # Click events only

    def to_algolia_event(self, index: AlgoliaIndex):
        return {
            "eventType": self.eventType,
            "eventName": self.eventName,
            "userToken": self.userToken,
            "index": index.value,
            "objectIDs": self.objectIDs,
            "positions": self.positions,
        }
