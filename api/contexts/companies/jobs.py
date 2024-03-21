from io import StringIO
from fastapi import APIRouter, Request, Depends, UploadFile, File
import pandas as pd

from ajb.base import QueryFilterParams, build_pagination_response
from ajb.contexts.companies.jobs.models import (
    UserCreateJob,
    Job,
    PaginatedJob,
)
from ajb.contexts.companies.jobs.repository import JobRepository
from ajb.contexts.companies.jobs.usecase import JobsUseCase

from api.vendors import mixpanel


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
    response = JobsUseCase(request.state.request_scope).create_job(company_id, job)
    mixpanel.job_created_from_portal(
        request.state.request_scope.user_id,
        company_id,
        response.id,
        response.position_title,
    )
    return response


@router.get("/{job_id}", response_model=Job)
def get_job(request: Request, company_id: str, job_id: str):
    return JobRepository(request.state.request_scope, company_id).get(job_id)


@router.put("/{job_id}", response_model=Job)
def update_job(request: Request, company_id: str, job_id: str, job: UserCreateJob):
    return JobsUseCase(request.state.request_scope).update_job(company_id, job_id, job)


@router.delete("/{job_id}")
def delete_job(request: Request, company_id: str, job_id: str):
    return JobsUseCase(request.state.request_scope).delete_job(company_id, job_id)


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
    job_repo = JobRepository(request.state.request_scope, company_id)
    return await _process_jobs_csv_file(company_id, file, job_repo)
