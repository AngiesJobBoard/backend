from fastapi import APIRouter, Request, Depends

from ajb.base import build_pagination_response
from ajb.contexts.companies.jobs.repository import JobRepository
from ajb.contexts.companies.jobs.models import (
    PaginatedJobsWithCompany,
    AdminSearchJobsWithCompany,
)


router = APIRouter(tags=["Admin Jobs"], prefix="/admin/admin-jobs")


@router.get("/", response_model=PaginatedJobsWithCompany)
def get_jobs(
    request: Request,
    job_id: str | None = None,
    query: AdminSearchJobsWithCompany = Depends(),
    is_live: bool = False,
    is_boosted: bool = False,
):
    results = JobRepository(request.state.request_scope).get_jobs_with_company(
        job_id, query, is_live, is_boosted
    )
    return build_pagination_response(
        results, query.page, query.page_size, request.url._url, PaginatedJobsWithCompany
    )
