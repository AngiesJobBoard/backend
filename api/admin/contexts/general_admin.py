"""
This module is for various admin capabilities which can be organized better llllaaattteeerrr
"""

from fastapi import APIRouter, Request, Body

from ajb.base.events import SourceServices
from ajb.contexts.companies.recruiters.repository import RecruiterRepository
from ajb.contexts.applications.repository import ApplicationRepository
from ajb.contexts.companies.jobs.repository import JobRepository
from ajb.contexts.companies.recruiters.models import (
    UserCreateRecruiter,
    CreateRecruiter,
    Recruiter,
)
from ajb.contexts.applications.models import ScanStatus
from ajb.contexts.applications.events import ApplicationEventProducer
from ajb.contexts.applications.extract_data.ai_extractor import (
    SyncronousAIResumeExtractor,
)
from api.exceptions import GenericHTTPException
from api.middleware import scope


router = APIRouter(tags=["Admin Etc."], prefix="/etc")


@router.post("/add-user-to-company", response_model=Recruiter)
def add_user_to_company(request: Request, payload: UserCreateRecruiter):
    return RecruiterRepository(scope(request)).create(
        CreateRecruiter(**payload.model_dump())
    )


@router.post("/rerun-resume-scan", response_model=bool)
def rerun_resume_scan(request: Request, application_id: str = Body(...)):
    application = ApplicationRepository(scope(request)).get(application_id)
    if application.resume_id is None:
        raise GenericHTTPException(
            status_code=400, detail="Application does not have a resume"
        )
    ApplicationEventProducer(
        scope(request), source_service=SourceServices.ADMIN
    ).company_uploads_resume(
        company_id=application.company_id,
        job_id=application.job_id,
        resume_id=application.resume_id,
        application_id=application.id,
    )
    return True


@router.post("/rerun-application-submission", response_model=bool)
def rerun_application_submission(request: Request, application_id: str = Body(...)):
    application = ApplicationRepository(scope(request)).get(application_id)
    ApplicationEventProducer(
        scope(request), source_service=SourceServices.ADMIN
    ).application_is_submitted(application.company_id, application.job_id, application.id)
    return True


@router.post("/update-resume-scan-text", response_model=bool)
async def update_resume_scan_text(
    request: Request,
    application_id: str = Body(...),
    new_text: str = Body(...),
    rerun_match: bool = Body(...),
):
    app_repo = ApplicationRepository(scope(request))
    original_application = app_repo.get(application_id)

    resume_information = (
        SyncronousAIResumeExtractor().get_candidate_profile_from_resume_text(new_text)
    )
    app_repo.update_application_with_parsed_information(
        application_id=original_application.id,
        resume_url=original_application.resume_url,
        raw_resume_text=new_text,
        resume_information=resume_information,  # type: ignore
    )
    if rerun_match:
        ApplicationEventProducer(
            scope(request), source_service=SourceServices.ADMIN
        ).application_is_submitted(
            original_application.company_id,
            original_application.job_id,
            original_application.id,
        )
    return True


@router.post("/update-application-score", response_model=bool)
def update_application_score(
    request: Request,
    application_id: str = Body(...),
    new_score: int = Body(...),
    new_score_reason: str = Body(...),
):
    app_repo = ApplicationRepository(scope(request))
    app_repo.update_fields(
        id=application_id,
        application_match_score=new_score,
        application_match_reason=new_score_reason,
        match_score_status=ScanStatus.COMPLETED.value,
    )
    return True


@router.post("/update-job-score", response_model=bool)
def update_job_score(
    request: Request,
    job_id: str = Body(...),
    new_score: int = Body(...),
    new_score_reason: str = Body(...),
):
    job_repo = JobRepository(scope(request))
    job_repo.update_fields(
        id=job_id,
        job_score=new_score,
        job_score_reason=new_score_reason,
    )
    return True
