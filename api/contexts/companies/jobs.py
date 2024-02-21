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
from ajb.contexts.applications.repository import CompanyApplicationRepository
from ajb.contexts.resumes.models import UserCreateResume
from ajb.contexts.resumes.usecase import ResumeUseCase
from api.exceptions import GenericHTTPException

from api.vendors import storage

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


async def _process_csv_file(
    company_id: str,
    job_id: str,
    file: UploadFile,
    application_repo: CompanyApplicationRepository,
):
    if file and file.filename and not file.filename.endswith(".csv"):
        return []
    content = await file.read()
    content = content.decode("utf-8")
    content = StringIO(content)
    df = pd.read_csv(content)
    raw_candidates = df.to_dict(orient="records")
    return application_repo.create_applications_from_csv(
        company_id, job_id, raw_candidates
    )


@router.post("/{job_id}/csv-upload")
async def upload_applications_from_csv(
    request: Request, company_id: str, job_id: str, files: list[UploadFile] = File(...)
):
    all_created_applications = []
    application_repo = CompanyApplicationRepository(request.state.request_scope)
    for file in files:
        all_created_applications.extend(
            await _process_csv_file(company_id, job_id, file, application_repo)
        )
    if not all_created_applications:
        raise HTTPException(status_code=400, detail="No valid applications found")
    return all_created_applications


@router.post("/pdf")
async def upload_applications_from_pdfs(
    request: Request, company_id: str, job_id: str, files: list[UploadFile] = File(...)
):
    files_processed = 0
    created_resume_files = []
    resume_usecase = ResumeUseCase(request.state.request_scope, storage)
    for file in files:
        if file and file.filename and not file.filename.endswith(".pdf"):
            continue
        created_resume = resume_usecase.create_resume(
            UserCreateResume(
                file_type=file.content_type or "application/pdf",
                file_name=file.filename or "resume.pdf",
                resume_data=file.file.read(),
                company_id=company_id,
                job_id=job_id,
            )
        )
        created_resume_files.append(created_resume)
        files_processed += 1
    if not files_processed:
        raise HTTPException(status_code=400, detail="No valid files found")
    return {"files_processed": files_processed, "resumes": created_resume_files}
