"""
This router is for use with jobs.angiesjobboard.com a public facing job board.
Jobs have to be manually set as public for their links to be accessible.
"""

from fastapi import APIRouter, Depends, UploadFile, File, Body, status
from ajb.contexts.companies.jobs.repository import JobRepository, FullJobWithCompany
from ajb.contexts.applications.usecase import (
    ApplicationUseCase,
    UserCreateResume,
    CreateApplication,
)

from ajb.base import RequestScope
from api.vendors import db, storage, kafka_producer
from api.exceptions import GenericHTTPException


JOB_APPLICATIONS_REQUEST_SCOPE = RequestScope(
    user_id="open_job_applications", db=db, kafka=kafka_producer
)

router = APIRouter(
    tags=["Open Job Applications"],
    prefix="/job-applications",
)


@router.get("/jobs/{job_id}", response_model=FullJobWithCompany)
def get_job(job_id: str):
    result = JobRepository(JOB_APPLICATIONS_REQUEST_SCOPE).get_full_job_with_company(
        job_id
    )
    if not result.job_is_public or result.active is False:
        raise GenericHTTPException(404, "Not found")
    return result


@router.post("/jobs/{job_id}/apply", status_code=status.HTTP_204_NO_CONTENT)
async def apply_to_job(
    job_id: str,
    email: str = Body(...),
    name: str = Body(...),
    phone_number: str = Body(...),
    resume: UploadFile = File(...),
):
    # Check job is valid public job first
    job = JobRepository(JOB_APPLICATIONS_REQUEST_SCOPE).get(job_id)
    if not job.job_is_public or job.active is False:
        raise GenericHTTPException(404, "Not found")

    # Now create the application
    data = await resume.read()
    filename = resume.filename
    content_type = resume.content_type
    file_end = filename.split(".")[-1]  # type: ignore
    ApplicationUseCase(JOB_APPLICATIONS_REQUEST_SCOPE).create_application_from_resume(
        data=UserCreateResume(
            file_type=content_type or file_end,
            file_name=filename or f"resume.{file_end}",
            resume_data=data,
            company_id=job.company_id,
            job_id=job_id,
        ),
        additional_partial_data=CreateApplication(
            email=email,
            name=name,
            phone=phone_number,
            job_id=job_id,
            company_id=job.company_id,
        ),
    )
    return status.HTTP_204_NO_CONTENT
