"""
This router is for use with jobs.angiesjobboard.com a public facing job board.
Jobs have to be manually set as public for their links to be accessible.

AJBTODO - this module could be cleaned up with a proper resolver class for handling the public form submission
"""

import json
from fastapi import APIRouter, UploadFile, File, Form, status
from ajb.contexts.companies.jobs.repository import FullJobWithCompany
from ajb.contexts.companies.jobs.public_application_forms.usecase import (
    JobPublicApplicationFormUsecase,
)
from ajb.contexts.companies.jobs.public_application_forms.models import (
    UserCreatePublicApplicationForm,
    PublicApplicationForm,
)
from ajb.contexts.resumes.models import UserCreateResume
from ajb.contexts.applications.models import CreateApplication
from ajb.contexts.applications.usecase import (
    ApplicationUseCase,
)

from ajb.base import RequestScope
from api.vendors import db, kafka_producer
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
    return JobPublicApplicationFormUsecase(
        JOB_APPLICATIONS_REQUEST_SCOPE
    ).get_public_job_data(job_id)


def get_partial_data_from_application_form(created_form_data: PublicApplicationForm):
    return CreateApplication(
        email=created_form_data.email,
        name=created_form_data.full_legal_name,
        phone=created_form_data.phone,
        job_id=created_form_data.job_id,
        company_id=created_form_data.company_id,
        application_form_id=created_form_data.id,
    )


async def handle_application_by_resume_file(
    resume: UploadFile, created_form_data: PublicApplicationForm
):
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
            job_id=created_form_data.job_id,
        ),
        additional_partial_data=get_partial_data_from_application_form(
            created_form_data
        ),
    )
    return status.HTTP_204_NO_CONTENT


def handle_application_by_resume_text(created_form_data: PublicApplicationForm):
    ApplicationUseCase(JOB_APPLICATIONS_REQUEST_SCOPE).create_application_from_raw_text(
        company_id=created_form_data.company_id,
        job_id=created_form_data.job_id,
        raw_text=str(created_form_data.resume_text),
        additional_partial_data=get_partial_data_from_application_form(
            created_form_data
        ),
    )
    return status.HTTP_204_NO_CONTENT


@router.post("/jobs/{job_id}/apply", status_code=status.HTTP_204_NO_CONTENT)
async def submit_public_application_form(
    job_id: str,
    form_data: str = Form(...),
    resume: UploadFile | None = File(None),
):
    # Save the raw form data
    created_form_data, updated_existing_applications = JobPublicApplicationFormUsecase(
        JOB_APPLICATIONS_REQUEST_SCOPE
    ).submit_public_job_application(
        UserCreatePublicApplicationForm.model_validate(json.loads(form_data)), job_id
    )
    if updated_existing_applications:
        return status.HTTP_204_NO_CONTENT

    # Now create the application based on either the resume file, provided resume text, or if neither throw an error
    if not resume and not created_form_data.resume_text:
        raise GenericHTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must provide either a resume file or resume text",
        )

    if resume:
        return await handle_application_by_resume_file(resume, created_form_data)
    return handle_application_by_resume_text(created_form_data)
