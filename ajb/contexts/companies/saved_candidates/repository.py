from typing import cast
from ajb.base import (
    MultipleChildrenRepository,
    Collection,
    RequestScope,
    RepositoryRegistry,
    QueryFilterParams,
    RepoFilterParams,
)
from ajb.base.events import SourceServices
from ajb.contexts.companies.events import CompanyEventProducer
from ajb.vendor.arango.models import Join
from .models import (
    SavedCandidate,
    CreateSavedCandidate,
    SavedCandidatesListObject,
    AlgoliaCandidateSearch,
    User,
)


class CompanySavesCandidateRepository(
    MultipleChildrenRepository[CreateSavedCandidate, SavedCandidate]
):
    collection = Collection.COMPANY_SAVES_CANDIDATES
    entity_model = SavedCandidate

    def __init__(self, request_scope: RequestScope, company_id: str):
        super().__init__(
            request_scope,
            parent_collection=Collection.COMPANIES.value,
            parent_id=company_id,
        )

    def create(self, data: CreateSavedCandidate, overridden_id: str | None = None) -> SavedCandidate:  # type: ignore
        saved_candidate = super().create(data, overridden_id)
        CompanyEventProducer(
            self.request_scope, SourceServices.API
        ).company_saves_candidate(candidate_id=data.user_id)
        return saved_candidate

    def query_with_candidates(
        self, query: QueryFilterParams | RepoFilterParams | None = None
    ):
        query = query or RepoFilterParams()
        results, count = self.query_with_joins(
            joins=[
                Join(
                    to_collection_alias="candidate",
                    to_collection="users",
                    from_collection_join_attr="user_id",
                ),
            ],
            repo_filters=query,
            return_model=SavedCandidatesListObject,
        )
        results = cast(list[SavedCandidatesListObject], results)

        # Convert all users to their algolia search version
        converted_results = []
        for res in results:
            converted_results.append(
                SavedCandidatesListObject(
                    **res.model_dump(exclude={"candidate"}),
                    candidate=(
                        AlgoliaCandidateSearch.convert_from_user(res.candidate)
                        if isinstance(res.candidate, User)
                        else res.candidate
                    )
                )
            )
        return converted_results, count


RepositoryRegistry.register(CompanySavesCandidateRepository)
