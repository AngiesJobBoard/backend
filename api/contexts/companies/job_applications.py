from io import StringIO
from fastapi import APIRouter, Request, UploadFile, File, HTTPException
import pandas as pd

from ajb.contexts.applications.usecase import ApplicationUseCase
from ajb.contexts.resumes.models import UserCreateResume
from ajb.contexts.resumes.usecase import ResumeUseCase

from api.vendors import storage


router = APIRouter(
    tags=["Company Job Applications"], prefix="/companies/{company_id}/jobs/{job_id}"
)


async def _process_applications_csv_file(
    company_id: str,
    job_id: str,
    file: UploadFile,
    application_usecase: ApplicationUseCase,
):
    if file and file.filename and not file.filename.endswith(".csv"):
        return []
    content = await file.read()
    content = content.decode("utf-8")
    content = StringIO(content)
    df = pd.read_csv(content)
    raw_candidates = df.to_dict(orient="records")
    return application_usecase.create_applications_from_csv(
        company_id, job_id, raw_candidates
    )


@router.post("/csv-upload")
async def upload_applications_from_csv(
    request: Request, company_id: str, job_id: str, files: list[UploadFile] = File(...)
):
    all_created_applications = []
    application_repo = ApplicationUseCase(request.state.request_scope)
    for file in files:
        all_created_applications.extend(
            await _process_applications_csv_file(
                company_id, job_id, file, application_repo
            )  # type: ignore
        )
    if not all_created_applications:
        raise HTTPException(status_code=400, detail="No valid applications found")
    return all_created_applications


@router.post("/resume")
async def upload_applications_from_resume(
    request: Request, company_id: str, job_id: str, files: list[UploadFile] = File(...)
):
    files_processed = 0
    created_applications = []
    application_usecase = ApplicationUseCase(request.state.request_scope, storage)
    for file in files:
        file_end = file.filename.split(".")[-1]  # type: ignore
        created_application = application_usecase.create_application_from_resume(
            UserCreateResume(
                file_type=file.content_type or file_end,
                file_name=file.filename or f"resume.{file_end}",
                resume_data=file.file.read(),
                company_id=company_id,
                job_id=job_id,
            )
        )
        created_applications.append(created_application)
        files_processed += 1
    if not files_processed:
        raise HTTPException(status_code=400, detail="No valid files found")
    return {"files_processed": files_processed, "applications": created_applications}
