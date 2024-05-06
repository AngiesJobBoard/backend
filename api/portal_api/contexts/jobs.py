from io import StringIO
from fastapi import APIRouter, Request, Depends, UploadFile, File, Body
import pandas as pd

from ajb.base import QueryFilterParams, build_pagination_response
from ajb.contexts.companies.jobs.models import (
    UserCreateJob,
    Job,
    PaginatedJob,
)
from ajb.contexts.companies.jobs.repository import JobRepository
from ajb.contexts.companies.jobs.usecase import JobsUseCase
from api.middleware import scope


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
    response = JobsUseCase(scope(request)).create_job(company_id, job)
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


async def _process_jobs_csv_file(
    company_id: str, file: UploadFile, job_repo: JobRepository
):
    if file and file.filename and not file.filename.endswith(".csv"):
        return []
    content = await file.read()
    content = content.decode("utf-8")
    content = StringIO(content)
    df = pd.read_csv(content)
    df = df.where(pd.notnull(df), None)
    raw_jobs = df.to_dict(orient="records")
    jobs = [UserCreateJob.from_csv(job) for job in raw_jobs]  # type: ignore
    return JobsUseCase(job_repo.request_scope).create_many_jobs(company_id, jobs)


@router.post("/jobs-from-csv")
async def create_jobs_from_csv_data(
    request: Request, company_id: str, file: UploadFile = File(...)
):
    job_repo = JobRepository(scope(request), company_id)
    return await _process_jobs_csv_file(company_id, file, job_repo)
