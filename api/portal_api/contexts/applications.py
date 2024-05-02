from fastapi import APIRouter, Request, Depends, Body

from ajb.base import (
    QueryFilterParams,
    RepoFilterParams,
    build_pagination_response,
    Pagination,
)
from ajb.base.events import SourceServices
from ajb.contexts.applications.models import (
    CompanyApplicationView,
    PaginatedDataReducedApplication,
    DataReducedApplication,
)
from ajb.contexts.applications.models import (
    CreateApplicationStatusUpdate,
    CompanyApplicationStatistics,
)
from ajb.contexts.applications.repository import (
    CompanyApplicationRepository,
    ApplicationRepository,
)
from ajb.contexts.applications.usecase import ApplicationUseCase
from ajb.contexts.applications.events import ApplicationEventProducer
from ajb.contexts.applications.extract_data.ai_extractor import (
    SyncronousAIResumeExtractor,
)
from ajb.vendor.arango.models import Filter, Operator

from api.middleware import scope
from api.exceptions import GenericHTTPException

router = APIRouter(
    tags=["Company Applications"], prefix="/companies/{company_id}/applications"
)


@router.get("/", response_model=PaginatedDataReducedApplication)
def get_all_company_applications(
    request: Request,
    company_id: str,
    job_id: str | None = None,
    match_score: int | None = None,
    new_only: bool = False,
    resume_text_contains: str | None = None,
    has_required_skill: str | None = None,
    status_filter: str | None = None,
    query: QueryFilterParams = Depends(),
):
    """Gets all applications"""
    results = CompanyApplicationRepository(scope(request)).get_company_view_list(
        company_id,
        query,
        job_id,
        match_score,
        new_only,
        resume_text_contains,
        has_required_skill,
        status_filter.split(",") if status_filter else None,
    )
    return build_pagination_response(
        results,
        query.page,
        query.page_size,
        request.url._url,
        PaginatedDataReducedApplication,
    )


@router.post("/pending", response_model=PaginatedDataReducedApplication)
def get_all_pending_applications(
    request: Request,
    company_id: str,
    job_id: str | None = Body(None),
    include_failed: bool = Body(False),
    page: int = 0,
    page_size: int = 25,
):
    """Gets all pending applications"""
    query = RepoFilterParams(
        pagination=Pagination(page=page, page_size=page_size),
    )
    results = CompanyApplicationRepository(scope(request)).get_all_pending_applications(
        company_id, query, job_id, include_failed
    )
    return build_pagination_response(
        results,
        page,
        page_size,
        request.url._url,
        PaginatedDataReducedApplication,
    )


@router.post("/many", response_model=PaginatedDataReducedApplication)
def get_many_company_applications(
    request: Request,
    company_id: str,
    application_ids: list[str],
    page: int = 0,
    page_size: int = 25,
):
    """Gets all applications by a list of ids"""
    query = RepoFilterParams(
        pagination=Pagination(page=page, page_size=page_size),
        filters=[
            Filter(field="_key", operator=Operator.ARRAY_IN, value=application_ids)
        ],
    )
    results = CompanyApplicationRepository(scope(request)).get_company_view_list(
        company_id, query
    )
    return build_pagination_response(
        results,
        page,
        page_size,
        request.url._url,
        PaginatedDataReducedApplication,
    )


@router.get("/count", response_model=int)
def get_application_counts(
    request: Request,
    company_id: str,
    job_id: str | None = None,
    minimum_match_score: int | None = None,
    new_only: bool = False,
):
    filter_params = RepoFilterParams(
        filters=[Filter(field="company_id", value=company_id)]
    )
    if job_id:
        filter_params.filters.append(Filter(field="job_id", value=job_id))
    if minimum_match_score:
        filter_params.filters.append(
            Filter(
                field="application_match_score",
                operator=Operator.GREATER_THAN_EQUAL,
                value=minimum_match_score,
            )
        )
    if new_only:
        filter_params.filters.append(
            Filter(field="application_status", operator=Operator.IS_NULL, value=None)
        )
    return CompanyApplicationRepository(scope(request)).get_count(filter_params)


@router.get("/statistics", response_model=CompanyApplicationStatistics)
def get_application_statistics(
    request: Request, company_id: str, job_id: str | None = None
):
    return ApplicationUseCase(scope(request)).get_application_statistics(
        company_id, job_id
    )


@router.get("/{application_id}", response_model=CompanyApplicationView)
def get_company_application(request: Request, company_id: str, application_id: str):
    """Gets a single application"""
    return CompanyApplicationRepository(scope(request)).get_company_view_single(
        application_id
    )


@router.delete("/{application_id}")
def delete_company_application(request: Request, company_id: str, application_id: str):
    """Deletes an application"""
    # First make sure that the application exists for this company
    response = ApplicationUseCase(scope(request)).delete_application_for_job(
        company_id, application_id
    )
    return response


@router.post("/{application_id}/rerun-resume-scan", response_model=bool)
def rerun_resume_scan(
    request: Request, company_id: str, application_id: str
):
    application = ApplicationRepository(scope(request)).get(application_id)
    if application.company_id != company_id:
        raise GenericHTTPException(status_code=400, detail="Application does not exist")
    if application.resume_id is None:
        raise GenericHTTPException(
            status_code=400, detail="Application does not have a resume"
        )
    ApplicationEventProducer(
        scope(request), source_service=SourceServices.API
    ).company_uploads_resume(
        company_id=application.company_id,
        job_id=application.job_id,
        resume_id=application.resume_id,
        application_id=application.id,
    )
    return True


@router.post("/{application_id}/rerun-match-score", response_model=bool)
def rerun_match_score(
    request: Request, company_id: str, application_id: str
):
    application = ApplicationRepository(scope(request)).get(application_id)
    if application.company_id != company_id:
        raise GenericHTTPException(status_code=400, detail="Application does not exist")
    ApplicationEventProducer(
        scope(request), source_service=SourceServices.API
    ).application_is_submitted(application.company_id, application.job_id, application.id)
    return True


@router.post("/update-resume-scan-text", response_model=bool)
async def update_resume_scan_text(
    request: Request,
    company_id: str,
    application_id: str,
    new_text: str = Body(...),
    rerun_match: bool = Body(...),
):
    app_repo = ApplicationRepository(scope(request))
    original_application = app_repo.get(application_id)
    if original_application.company_id != company_id:
        raise GenericHTTPException(status_code=400, detail="Application does not exist")

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


@router.post(
    "/jobs/{job_id}/applications/{application_id}/status",
    response_model=DataReducedApplication,
)
def update_application_status(
    request: Request,
    company_id: str,
    job_id: str,
    application_id: str,
    new_status: CreateApplicationStatusUpdate,
):
    """Updates an application status"""
    return ApplicationUseCase(scope(request)).recruiter_updates_application_status(
        company_id, job_id, application_id, new_status
    )
