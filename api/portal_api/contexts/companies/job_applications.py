from io import StringIO
from fastapi import (
    APIRouter,
    Request,
    UploadFile,
    File,
    HTTPException,
    Body,
    BackgroundTasks,
)
import pandas as pd

from ajb.contexts.applications.usecase import ApplicationUseCase
from ajb.contexts.resumes.models import UserCreateResume

from api.vendors import storage
from api.middleware import scope


router = APIRouter(
    tags=["Company Job Applications"], prefix="/companies/{company_id}/jobs/{job_id}"
)


@router.post("/resume")
async def upload_applications_from_resume(
    background_tasks: BackgroundTasks,
    request: Request,
    company_id: str,
    job_id: str,
    files: list[UploadFile] = File(...),
):
    application_usecase = ApplicationUseCase(scope(request), storage)
    files_processed = 0

    for file in files:
        data = await file.read()  # Read file data in the main function
        background_tasks.add_task(
            process_resume_file,
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
    application_usecase, filename, content_type, data, company_id, job_id
):
    file_end = filename.split(".")[-1]
    try:
        created_application = application_usecase.create_application_from_resume(
            UserCreateResume(
                file_type=content_type or file_end,
                file_name=filename or f"resume.{file_end}",
                resume_data=data,
                company_id=company_id,
                job_id=job_id,
            )
        )
        return created_application
    except Exception as e:
        print(f"Failed to process file {filename}: {str(e)}")


@router.post("/raw")
async def upload_application_from_text_dump(
    request: Request, company_id: str, job_id: str, text: str = Body(...)
):
    return ApplicationUseCase(scope(request)).application_is_created_from_raw_text(
        company_id, job_id, text
    )
