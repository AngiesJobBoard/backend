from fastapi import (
    APIRouter,
    Request,
    UploadFile,
    File,
    Body,
)

from ajb.contexts.applications.usecase import ApplicationUseCase
from ajb.contexts.resumes.models import UserCreateResume
from ajb.contexts.billing.validate_usage import BillingValidateUsageUseCase, UsageType
from ajb.exceptions import TierLimitHitException

from api.exceptions import TierLimitHTTPException
from api.middleware import scope


router = APIRouter(
    tags=["Company Job Applications"], prefix="/companies/{company_id}/jobs/{job_id}"
)


@router.post("/resume")
async def upload_applications_from_resume(
    request: Request,
    company_id: str,
    job_id: str,
    files: list[UploadFile] = File(...),
):
    try:
        BillingValidateUsageUseCase(scope(request), company_id).validate_usage(
            company_id, UsageType.APPLICATIONS_PROCESSED
        )
    except TierLimitHitException:
        raise TierLimitHTTPException
    application_usecase = ApplicationUseCase(scope(request))
    files_processed = 0

    for file in files:
        data = await file.read()
        process_resume_file(
            application_usecase,
            file.filename,
            file.content_type,
            data,
            company_id,
            job_id,
        )
        files_processed += 1

    return {"message": "Files are being processed", "files_processed": files_processed}


def process_resume_file(
    application_usecase: ApplicationUseCase,
    filename: str | None,
    content_type: str | None,
    data: bytes,
    company_id: str,
    job_id: str,
):
    file_end = filename.split(".")[-1] if filename else "pdf"
    created_application = application_usecase.create_application_from_resume(
        UserCreateResume(
            file_type=content_type or file_end,
            file_name=filename or f"resume.{file_end}",
            resume_data=data,
            company_id=company_id,
            job_id=job_id,
        ),
    )
    return created_application


@router.post("/raw")
async def upload_application_from_text_dump(
    request: Request, company_id: str, job_id: str, text: str = Body(...)
):
    try:
        BillingValidateUsageUseCase(scope(request), company_id).validate_usage(
            company_id, UsageType.APPLICATIONS_PROCESSED
        )
    except TierLimitHitException:
        raise TierLimitHTTPException
    return ApplicationUseCase(scope(request)).application_is_created_from_raw_text(
        company_id, job_id, text
    )
