from io import StringIO
from fastapi import APIRouter, Request, Depends, UploadFile, File, HTTPException
import pandas as pd

from ajb.base import QueryFilterParams, build_pagination_response
from ajb.contexts.companies.jobs.models import (
    UserCreateJob,
    CreateJob,
    Job,
    PaginatedJob,
)
from ajb.contexts.companies.jobs.repository import JobRepository
from ajb.contexts.applications.models import CreateApplication
from ajb.contexts.applications.repository import ApplicationRepository
from ajb.contexts.applications.matching.usecase import ApplicantMatchUsecase
from api.exceptions import GenericHTTPException

from api.vendors import openai

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
        jobs = [UserCreateJob(**job) for job in raw_jobs]  # type: ignore
        return JobRepository(request.state.request_scope, company_id).create_many_jobs(
            company_id, jobs
        )
    except Exception as e:
        raise GenericHTTPException(
            status_code=400, detail=f"Error processing file: {e}"
        )


# @router.post("/manual")
# def create_application(request: Request, company_id: str, application: UserCreatedApplication):
#     ...


@router.post("/{job_id}/csv-upload")
async def upload_applications_from_csv(
    request: Request, company_id: str, job_id: str, files: list[UploadFile] = File(...)
):
    files_processed = 0
    all_created_applications = []
    application_repo = ApplicationRepository(request.state.request_scope)
    for file in files:
        if file and file.filename and not file.filename.endswith(".csv"):
            continue
        content = await file.read()
        content = content.decode("utf-8")
        content = StringIO(content)
        df = pd.read_csv(content)
        df = df.where(pd.notnull(df), None)
        raw_candidates = df.to_dict(orient="records")
        candidates = [
            CreateApplication.from_csv_record(company_id, job_id, candidate)
            for candidate in raw_candidates
        ]
        created_applications = application_repo.create_many(candidates)
        all_created_applications.extend(created_applications)
        files_processed += 1
    if not files_processed:
        raise HTTPException(status_code=400, detail="No valid files found")
    
    matcher_usecase = ApplicantMatchUsecase(request.state.request_scope, openai)
    matcher_usecase.update_many_applications_with_match_scores(
        [created_application for created_application in all_created_applications], job_id
    )
    return {"files_processed": files_processed, "created_applications": all_created_applications}


# @router.post("/pdf")
# async def upload_applications_from_pdfs(request: Request, company_id: str, job_id: str, files: list[UploadFile] = File(...)):
#     files_processed = 0
#     for file in files:
#         if file and file.filename and not file.filename.endswith('.csv'):
#             continue
#         print("Working on file", file.filename)
#         files_processed += 1
#     if not files_processed:
#         raise HTTPException(status_code=400, detail="No valid files found")
#     return {"files_processed": files_processed}
