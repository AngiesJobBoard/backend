from pydantic import BaseModel

from ajb.contexts.users.models import (
    AlgoliaCandidateSearch,
    WorkSettingEnum,
)
from ajb.vendor.algolia.models import AlgoliaSearchParams, AlgoliaSearchResults


class CandidateSearchContext(BaseModel):
    recruiter_user_id: str


class CandidateSearchParams(AlgoliaSearchParams):
    most_recent_job_title: str | None = None
    most_recent_company: str | None = None
    skills: str | None = None  # This is an array?
    licenses: str | None = None  # This is an array?
    certifications: str | None = None  # This is an array?
    languages: str | None = None  # This is an array?

    desired_job_title: str | None = None
    minimum_hourly_desired_pay: float | None = None
    willing_to_relocate: bool | None = None
    # desired_work_settings: list[WorkSettingEnum] | None = None
    # desired_industries: list[str] | None = None
    ready_to_start_immediately: bool | None = None

    def to_algolia_search(self, context: CandidateSearchContext) -> AlgoliaSearchParams:
        # filter_dict = {}
        # if self.most_recent_job_title:
        #     filter_dict["most_recent_job_title"] = self.most_recent_job_title
        # if self.most_recent_company:
        #     filter_dict["most_recent_company"] = self.most_recent_company
        # if self.skills:
        #     filter_dict["skills"] = self.skills
        # if self.licenses:
        #     filter_dict["licenses"] = self.licenses
        # if self.certifications:
        #     filter_dict["certifications"] = self.certifications
        # if self.languages:
        #     filter_dict["languages"] = self.languages

        # if self.desired_job_title:
        #     filter_dict["desired_job_title"] = self.desired_job_title
        # if self.minimum_hourly_desired_pay:
        #     filter_dict["minimum_hourly_desired_pay"] = self.minimum_hourly_desired_pay
        # if self.willing_to_relocate:
        #     filter_dict["willing_to_relocate"] = self.willing_to_relocate
        # if self.desired_work_settings:
        #     filter_dict["desired_work_settings"] = self.desired_work_settings
        # if self.desired_industries:
        #     filter_dict["desired_industries"] = self.desired_industries
        # if self.ready_to_start_immediately:
        #     filter_dict["ready_to_start_immediately"] = self.ready_to_start_immediately

        return AlgoliaSearchParams(
            query=self.query,
            # filters=filter_dict,
            user_id=context.recruiter_user_id,
        )


class AlgoliaCandidateSearchResults(AlgoliaSearchResults):
    hits: list[AlgoliaCandidateSearch]

    @classmethod
    def convert_from_algolia(cls, algolia_results: AlgoliaSearchResults):
        return cls(
            hits=[
                AlgoliaCandidateSearch.model_validate(hit)
                for hit in algolia_results.hits
            ],
            nbHits=algolia_results.nbHits,
            page=algolia_results.page,
            nbPages=algolia_results.nbPages,
            hitsPerPage=algolia_results.hitsPerPage,
            exhaustiveNbHits=algolia_results.exhaustiveNbHits,
        )
