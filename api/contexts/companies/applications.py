from fastapi import (
    APIRouter,
    Request,
    Depends,
)

from ajb.base import (
    QueryFilterParams,
    RepoFilterParams,
    build_pagination_response,
)
from ajb.contexts.applications.models import (
    CompanyApplicationView,
    PaginatedDataReducedApplication,
    DataReducedApplication,
)
from ajb.contexts.applications.recruiter_updates.repository import (
    RecruiterUpdatesRepository,
)
from ajb.contexts.applications.recruiter_updates.models import (
    UserCreateRecruiterComment,
)
from ajb.contexts.applications.models import (
    CreateApplicationStatusUpdate,
)
from ajb.contexts.applications.repository import CompanyApplicationRepository
from ajb.contexts.applications.usecase import ApplicationUseCase
from ajb.vendor.arango.models import Filter, Operator

from api.vendors import mixpanel


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
    results = CompanyApplicationRepository(
        request.state.request_scope
    ).get_company_view_list(
        company_id,
        query,
        job_id,
        match_score,
        new_only,
        resume_text_contains,
        has_required_skill,
        status_filter,
    )
    return build_pagination_response(
        results,
        query.page,
        query.page_size,
        request.url._url,
        PaginatedDataReducedApplication,
    )


@router.post("/many", response_model=PaginatedDataReducedApplication)
def get_many_company_applications(
    request: Request,
    company_id: str,
    application_ids: list[str],
    page: int = 0,
    page_size: int = 50,
):
    """Gets all applications by a list of ids"""
    query = RepoFilterParams(
        filters=[
            Filter(field="_key", operator=Operator.ARRAY_IN, value=application_ids)
        ],
    )
    results = CompanyApplicationRepository(
        request.state.request_scope
    ).get_company_view_list(company_id, query)
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
    return CompanyApplicationRepository(request.state.request_scope).get_count(
        filter_params
    )


@router.get("/{application_id}", response_model=CompanyApplicationView)
def get_company_application(request: Request, company_id: str, application_id: str):
    """Gets a single application"""
    return CompanyApplicationRepository(
        request.state.request_scope
    ).get_company_view_single(application_id)


@router.delete("/{application_id}")
def delete_company_application(request: Request, company_id: str, application_id: str):
    """Deletes an application"""
    # First make sure that the application exists for this company
    response = ApplicationUseCase(
        request.state.request_scope
    ).delete_application_for_job(company_id, application_id)
    mixpanel.application_is_deleted(
        request.state.request_scope.user_id, company_id, response.job_id, response.id
    )
    return response


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
    response = ApplicationUseCase(
        request.state.request_scope
    ).recruiter_updates_application_status(
        company_id, job_id, application_id, new_status
    )
    mixpanel.application_status_is_updated(
        request.state.request_scope.user_id,
        company_id,
        job_id,
        application_id,
        new_status.application_status,
    )
    return response
