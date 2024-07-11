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
    application_usecase = ApplicationUseCase(scope(request))
    files_processed = 0

    for file in files:
        data = await file.read()
        filename = file.filename
        content_type = file.content_type
        file_end = filename.split(".")[-1] if filename else "pdf"
        try:
            application_usecase.create_application_from_resume(
                UserCreateResume(
                    file_type=content_type or file_end,
                    file_name=filename or f"resume.{file_end}",
                    resume_data=data,
                    company_id=company_id,
                    job_id=job_id,
                ),
            )
        except TierLimitHitException:
            raise TierLimitHTTPException
        files_processed += 1

    return {"message": "Files are being processed", "files_processed": files_processed}


@router.post("/raw")
async def upload_application_from_text_dump(
    request: Request, company_id: str, job_id: str, text: str = Body(...)
):
    try:
        return ApplicationUseCase(scope(request)).create_application_from_raw_text(
            company_id, job_id, text
        )
    except TierLimitHitException:
        raise TierLimitHTTPException
