from fastapi import APIRouter, Request, Depends

from ajb.vendor.algolia.models import (
    AlgoliaSearchResults,
    AlgoliaFacetSearchResults,
)
from ajb.contexts.search.jobs.search_repository import JobSearchRepository
from ajb.contexts.search.jobs.models import (
    SearchJobsParams,
    JobSearchContext,
    AlgoliaJobSearchResults,
    AlgoliaJobRecord,
)


from api.vendors import search_jobs


router = APIRouter(tags=["Search"], prefix="/search/jobs")


@router.get("/", response_model=AlgoliaJobSearchResults)
def search_jobs_endpoint(request: Request, query: SearchJobsParams = Depends()):
    """Searches for jobs"""
    context = JobSearchContext(user_id=request.state.request_scope.user_id)
    return JobSearchRepository(
        request.state.request_scope,
        search_jobs,
    ).search(context, query)


@router.get("/autocomplete", response_model=AlgoliaSearchResults)
def jobs_autocomplete(query: str):
    """Autocompletes a job search"""
    return search_jobs.autocomplete(query, ["position_title"])


@router.get("/categories", response_model=AlgoliaFacetSearchResults)
def search_job_categories(request: Request, search: str = ""):
    """Gets the job categories"""
    return JobSearchRepository(
        request.state.request_scope,
        search_jobs,
    ).search_job_categories(search)


@router.get("/{job_id}", response_model=AlgoliaJobRecord)
def get_job(request: Request, job_id: str):
    """Gets a job by id"""
    return JobSearchRepository(
        request.state.request_scope,
        search_jobs,
    ).get_job(job_id)
