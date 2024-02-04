from fastapi import APIRouter, Request, Depends

from ajb.base import QueryFilterParams, build_pagination_response
from ajb.contexts.companies.jobs.models import (
    UserCreateJob,
    CreateJob,
    Job,
    PaginatedJob,
)
from ajb.contexts.companies.jobs.repository import JobRepository
from ajb.contexts.companies.jobs.usecase import JobUseCase
from ajb.exceptions import FailedToPostJobException
from api.exceptions import GenericHTTPException


router = APIRouter(tags=["Company Jobs"], prefix="/companies/{company_id}/jobs")


@router.get("/", response_model=PaginatedJob)
def get_all_jobs(
    request: Request, company_id: str, query: QueryFilterParams = Depends()
):
    response = JobRepository(request.state.request_scope, company_id).get_company_jobs(
        company_id, query
    )
    return build_pagination_response(
        response, query.page, query.page_size, request.url._url, PaginatedJob
    )


@router.post("/", response_model=Job)
def create_job(request: Request, company_id: str, job: UserCreateJob):
    job_to_create = CreateJob(**job.model_dump(), company_id=company_id)
    job_to_create.job_score = job.calculate_score()
    return JobRepository(request.state.request_scope, company_id).create(job_to_create)


@router.get("/autocomplete")
def get_job_autocomplete(
    request: Request, company_id: str, prefix: str, field: str = "position_title"
):
    """Gets a list of jobs that match the prefix"""
    return JobRepository(request.state.request_scope, company_id).get_autocomplete(
        field, prefix
    )


@router.post("/submit-many")
def submit_many_jobs(request: Request, company_id: str, job_ids: list[str]):
    return JobUseCase(request.state.request_scope).submit_many_jobs_for_approval(
        company_id, job_ids
    )


@router.get("/{job_id}", response_model=Job)
def get_job(request: Request, company_id: str, job_id: str):
    return JobRepository(request.state.request_scope, company_id).get(job_id)


@router.patch("/{job_id}", response_model=Job)
def update_job(request: Request, company_id: str, job_id: str, job: UserCreateJob):
    return JobUseCase(request.state.request_scope).update_job(company_id, job_id, job)


@router.delete("/{job_id}")
def delete_job(request: Request, company_id: str, job_id: str):
    return JobRepository(request.state.request_scope, company_id).delete(job_id)


@router.post("/{job_id}/submit")
def submit_job(request: Request, company_id: str, job_id: str):
    try:
        return JobUseCase(request.state.request_scope).submit_job_for_approval(
            company_id, job_id
        )
    except FailedToPostJobException as exc:
        raise GenericHTTPException(status_code=400, detail=str(exc))


@router.post("/{job_id}/unsubmit")
def unsubmit_job(request: Request, company_id: str, job_id: str):
    return JobUseCase(request.state.request_scope).remove_job_submission(
        company_id, job_id
    )


@router.post("/{job_id}/unpost")
def unpost_job(request: Request, company_id: str, job_id: str):
    return JobUseCase(request.state.request_scope).unpost_job(company_id, job_id)
