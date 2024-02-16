from io import StringIO
from fastapi import APIRouter, Request, Depends, File, UploadFile
import pandas as pd

from ajb.base import QueryFilterParams, build_pagination_response
from ajb.contexts.companies.jobs.models import (
    UserCreateJob,
    CreateJob,
    Job,
    PaginatedJob,
)
from ajb.contexts.companies.jobs.repository import JobRepository
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


@router.get("/{job_id}", response_model=Job)
def get_job(request: Request, company_id: str, job_id: str):
    return JobRepository(request.state.request_scope, company_id).get(job_id)


@router.delete("/{job_id}")
def delete_job(request: Request, company_id: str, job_id: str):
    return JobRepository(request.state.request_scope, company_id).delete(job_id)


@router.post("/jobs-from-csv")
async def create_jobs_from_csv_data(
    request: Request, company_id: str, file: UploadFile = File(...)
):
    if file.content_type != "text/csv":
        raise GenericHTTPException(
            status_code=400, detail="Invalid file type. Please upload a CSV file."
        )

    try:
        content = await file.read()
        content = content.decode("utf-8")
        content = StringIO(content)
        df = pd.read_csv(content)
        df = df.where(pd.notnull(df), None)
        raw_jobs = df.to_dict(orient="records")
        print(f"\n\n{raw_jobs}\n\n")
        jobs = [UserCreateJob(**job) for job in raw_jobs]  # type: ignore
        return JobRepository(request.state.request_scope).create_many_jobs(
            company_id, jobs
        )
    except Exception as e:
        raise GenericHTTPException(
            status_code=400, detail=f"Error processing file: {e}"
        )
