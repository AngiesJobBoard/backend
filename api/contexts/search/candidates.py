from fastapi import APIRouter, Request, Depends

from ajb.contexts.search.candidates.search_repository import (
    CandidateSearchRepository,
)
from ajb.contexts.search.candidates.models import (
    CandidateSearchContext,
    CandidateSearchParams,
    AlgoliaCandidateSearchResults,
    AlgoliaCandidateSearch,
)

from api.vendors import search_candidates


router = APIRouter(tags=["Search"], prefix="/search/candidates")


@router.get("/", response_model=AlgoliaCandidateSearchResults)
def search_candidates_endpoint(
    request: Request, query: CandidateSearchParams = Depends()
):
    """Searches for candidates"""
    context = CandidateSearchContext(
        recruiter_user_id=request.state.request_scope.user_id
    )
    return CandidateSearchRepository(
        request.state.request_scope,
        search_candidates,
    ).search(context, query)


@router.get("/{candidate_id}", response_model=AlgoliaCandidateSearch)
def get_candidate(request: Request, candidate_id: str):
    """Gets a candidate by id"""
    return CandidateSearchRepository(
        request.state.request_scope,
        search_candidates,
    ).get_candidate(candidate_id)
