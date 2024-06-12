"""
This router is for use with jobs.angiesjobboard.com a public facing job board.
Jobs have to be manually set as public for their links to be accessible.
"""

from fastapi import APIRouter, UploadFile, File, Body, status
from ajb.contexts.companies.jobs.repository import FullJobWithCompany
from ajb.contexts.companies.jobs.public_application_forms.usecase import (
    JobPublicApplicationFormUsecase,
)
from ajb.contexts.companies.jobs.public_application_forms.models import (
    UserCreatePublicApplicationForm,
)
from ajb.contexts.resumes.models import UserCreateResume
from ajb.contexts.applications.models import CreateApplication
from ajb.contexts.applications.usecase import (
    ApplicationUseCase,
)

from ajb.base import RequestScope
from api.vendors import db, kafka_producer


JOB_APPLICATIONS_REQUEST_SCOPE = RequestScope(
    user_id="open_job_applications", db=db, kafka=kafka_producer
)

router = APIRouter(
    tags=["Open Job Applications"],
    prefix="/job-applications",
)


@router.get("/jobs/{job_id}", response_model=FullJobWithCompany)
def get_job(job_id: str):
    return JobPublicApplicationFormUsecase(
        JOB_APPLICATIONS_REQUEST_SCOPE
    ).get_public_job_data(job_id)


@router.post("/jobs/{job_id}/apply", status_code=status.HTTP_204_NO_CONTENT)
async def apply_to_job(
    job_id: str,
    form_data: UserCreatePublicApplicationForm = Body(...),
    resume: UploadFile = File(...),
):
    # Save the raw form data
    created_form_data = JobPublicApplicationFormUsecase(
        JOB_APPLICATIONS_REQUEST_SCOPE
    ).submit_public_job_application(form_data, job_id)

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
            company_id=created_form_data.company_id,
            job_id=job_id,
        ),
        additional_partial_data=CreateApplication(
            email=created_form_data.email,
            name=created_form_data.full_legal_name,
            phone=created_form_data.phone,
            job_id=job_id,
            company_id=created_form_data.job_id,
            application_form_id=created_form_data.id,
        ),
    )
    return status.HTTP_204_NO_CONTENT
