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
from api.exceptions import GenericHTTPException


router = APIRouter(tags=["Admin Etc."], prefix="/admin/etc")


@router.post("/add-user-to-company", response_model=Recruiter)
def add_user_to_company(request: Request, payload: UserCreateRecruiter):
    return RecruiterRepository(request_scope=request.state.request_scope).create(
        CreateRecruiter(**payload.model_dump())
    )


@router.post("/rerun-resume-scan", response_model=bool)
def rerun_resume_scan(request: Request, application_id: str = Body(...)):
    application = ApplicationRepository(request.state.request_scope).get(application_id)
    if application.resume_id is None:
        raise GenericHTTPException(
            status_code=400, detail="Application does not have a resume"
        )
    ApplicationEventProducer(
        request.state.request_scope, source_service=SourceServices.ADMIN
    ).company_uploads_resume(
        job_id=application.job_id,
        resume_id=application.resume_id,
        application_id=application.id,
    )
    return True


@router.post("/rerun-application-submission", response_model=bool)
def rerun_application_submission(request: Request, application_id: str = Body(...)):
    application = ApplicationRepository(request.state.request_scope).get(application_id)
    ApplicationEventProducer(
        request.state.request_scope, source_service=SourceServices.ADMIN
    ).application_is_created(application.company_id, application.job_id, application.id)
    return True


@router.post("/update-resume-scan-text", response_model=bool)
def update_resume_scan_text(
    request: Request,
    application_id: str = Body(...),
    new_text: str = Body(...),
    rerun_match: bool = Body(...),
):
    app_repo = ApplicationRepository(request.state.request_scope)
    application = app_repo.update_fields(
        id=application_id,
        extracted_resume_text=new_text,
    )
    if rerun_match:
        ApplicationEventProducer(
            request.state.request_scope, source_service=SourceServices.ADMIN
        ).application_is_created(
            application.company_id, application.job_id, application.id
        )
    return True


@router.post("/update-application-score", response_model=bool)
def update_application_score(
    request: Request,
    application_id: str = Body(...),
    new_score: int = Body(...),
    new_score_reason: str = Body(...),
):
    app_repo = ApplicationRepository(request.state.request_scope)
    app_repo.update_fields(
        id=application_id,
        application_match_score=new_score,
        application_match_reason=new_score_reason,
        match_score_status=ScanStatus.COMPLETED.value
    )
    return True


@router.post("/update-job-score", response_model=bool)
def update_job_score(
    request: Request,
    job_id: str = Body(...),
    new_score: int = Body(...),
    new_score_reason: str = Body(...),
):
    job_repo = JobRepository(request.state.request_scope)
    job_repo.update_fields(
        id=job_id,
        job_score=new_score,
        job_score_reason=new_score_reason,
    )
    return True
