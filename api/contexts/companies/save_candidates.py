from fastapi import APIRouter, Request, Depends

from ajb.base import QueryFilterParams, build_pagination_response
from ajb.contexts.companies.saved_candidates.models import (
    CreateSavedCandidate,
    SavedCandidate,
    SavedCandidatesPaginatedResponse,
)
from ajb.contexts.companies.saved_candidates.repository import (
    CompanySavesCandidateRepository,
)


router = APIRouter(
    tags=["Company Saves Candidates"], prefix="/companies/{company_id}/saved-candidates"
)


@router.get("/", response_model=SavedCandidatesPaginatedResponse)
def get_all_saved_candidates(
    request: Request, company_id: str, query: QueryFilterParams = Depends()
):
    """Gets the saved candidates for the current user"""
    results = CompanySavesCandidateRepository(
        request.state.request_scope, company_id
    ).query_with_candidates(query)
    return build_pagination_response(
        results,
        query.page,
        query.page_size,
        request.url._url,
        SavedCandidatesPaginatedResponse,
    )


@router.post("/", response_model=SavedCandidate)
def create_saved_candidate(
    request: Request, company_id: str, saved_job: CreateSavedCandidate
):
    """Creates a saved candidate for the current company"""
    return CompanySavesCandidateRepository(
        request.state.request_scope, company_id
    ).create(saved_job)


@router.delete("/{saved_job_id}")
def delete_saved_candidate(request: Request, company_id: str, saved_job_id: str):
    """Deletes a saved candidate for the current company"""
    return CompanySavesCandidateRepository(
        request.state.request_scope, company_id
    ).delete(saved_job_id)
