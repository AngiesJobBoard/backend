from fastapi import APIRouter, Request, Depends, Body

from ajb.base import QueryFilterParams, build_pagination_response
from ajb.contexts.companies.jobs.models import (
    UserCreateJob,
    Job,
    PaginatedJob,
)
from ajb.contexts.companies.jobs.repository import JobRepository
from ajb.contexts.companies.jobs.usecase import JobsUseCase
from ajb.exceptions import TierLimitHitException, FeatureNotAvailableOnTier

from api.middleware import scope
from api.exceptions import TierLimitHTTPException, FeatureNotAvailableOnTierHTTPException


router = APIRouter(tags=["Company Jobs"], prefix="/companies/{company_id}/jobs")


@router.get("/", response_model=PaginatedJob)
def get_all_jobs(
    request: Request,
    company_id: str,
    job_is_active_status: bool | None = None,
    query: QueryFilterParams = Depends(),
):
    response = JobRepository(scope(request), company_id).get_company_jobs(
        company_id, job_is_active_status, query
    )
    return build_pagination_response(
        response, query.page, query.page_size, request.url._url, PaginatedJob
    )


@router.post("/", response_model=Job)
def create_job(request: Request, company_id: str, job: UserCreateJob):
    try:
        response = JobsUseCase(scope(request)).create_job(company_id, job)
    except TierLimitHitException:
        raise TierLimitHTTPException
    return response


@router.get("/{job_id}", response_model=Job)
def get_job(request: Request, company_id: str, job_id: str):
    return JobRepository(scope(request), company_id).get(job_id)


@router.put("/{job_id}", response_model=Job)
def update_job(request: Request, company_id: str, job_id: str, job: UserCreateJob):
    return JobsUseCase(scope(request)).update_job(company_id, job_id, job)


@router.post("/{job_id}/mark-inactive", response_model=Job)
def mark_job_as_inactive(request: Request, company_id: str, job_id: str):
    return JobsUseCase(scope(request)).update_job_active_status(
        company_id, job_id, False
    )


@router.post("/{job_id}/mark-active", response_model=Job)
def mark_job_as_active(request: Request, company_id: str, job_id: str):
    return JobsUseCase(scope(request)).update_job_active_status(
        company_id, job_id, True
    )


@router.post("/{job_id}/toggle-public-page", response_model=Job)
def toggle_job_public_page(
    request: Request, company_id: str, job_id: str, is_available: bool = Body(...)
):
    try:
        return JobsUseCase(scope(request)).toggle_job_public_application_form(
            company_id, job_id, is_available
        )
    except FeatureNotAvailableOnTier:
        raise FeatureNotAvailableOnTierHTTPException
