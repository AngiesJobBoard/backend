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
from ajb.contexts.applications.enumerations import ApplicationQuickStatus
from ajb.contexts.applications.recruiter_updates.repository import (
    RecruiterUpdatesRepository,
)
from ajb.contexts.applications.recruiter_updates.models import (
    UserCreateRecruiterComment,
)
from ajb.contexts.applications.repository import ApplicationRepository
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
    shortlist_only: bool = False,
    match_score: int | None = None,
    new_only: bool = False,
    resume_text_contains: str | None = None,
    has_required_skill: str | None = None,
    query: QueryFilterParams = Depends(),
):
    """Gets all applications"""
    results = CompanyApplicationRepository(
        request.state.request_scope
    ).get_company_view_list(
        company_id,
        query,
        job_id,
        shortlist_only,
        match_score,
        new_only,
        resume_text_contains,
        has_required_skill,
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
    shortlist_only: bool = False,
    unviewed_only: bool = False,
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
    if shortlist_only:
        filter_params.filters.append(
            Filter(field="application_is_shortlisted", value=True)
        )
    if unviewed_only:
        filter_params.filters.append(Filter(field="viewed_by_company", value=False))
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


@router.patch("/jobs/{job_id}/applications/{application_id}/add-shortlist")
def add_application_to_shortlist(
    request: Request,
    company_id: str,
    job_id: str,
    application_id: str,
    comment: UserCreateRecruiterComment | None = None,
):
    response = ApplicationUseCase(
        request.state.request_scope
    ).company_updates_application_shortlist(company_id, application_id, True)
    mixpanel.application_is_shortlisted(
        request.state.request_scope.user_id, company_id, response.job_id, application_id
    )
    RecruiterUpdatesRepository(
        request.state.request_scope, application_id
    ).add_to_shortlist(
        company_id,
        job_id,
        application_id,
        request.state.request_scope.user_id,
        comment.comment if comment else None,
    )
    return response


@router.patch("/jobs/{job_id}/applications/{application_id}/remove-shortlist")
def remove_application_to_shortlist(
    request: Request,
    company_id: str,
    job_id: str,
    application_id: str,
    comment: UserCreateRecruiterComment | None = None,
):
    response = ApplicationUseCase(
        request.state.request_scope
    ).company_updates_application_shortlist(company_id, application_id, False)
    RecruiterUpdatesRepository(
        request.state.request_scope, application_id
    ).remove_from_shortlist(
        company_id,
        job_id,
        application_id,
        request.state.request_scope.user_id,
        comment.comment if comment else None,
    )
    return response


@router.post(
    "/jobs/{job_id}/applications/{application_id}/quick-status",
    response_model=DataReducedApplication,
)
def update_application_quick_status(
    request: Request,
    company_id: str,
    job_id: str,
    application_id: str,
    new_quick_status: ApplicationQuickStatus,
):
    """Updates an application quick status"""
    # AJBTODO Move this to unit of work and make recruiter update async??
    ApplicationRepository(request.state.request_scope).update_fields(
        application_id, application_quick_status=new_quick_status.value
    )
    mixpanel.application_quick_status_is_updated(
        request.state.request_scope.user_id,
        company_id,
        job_id,
        application_id,
        new_quick_status.value,
    )
    RecruiterUpdatesRepository(
        request.state.request_scope, application_id
    ).update_application_quick_status(
        company_id,
        job_id,
        application_id,
        request.state.request_scope.user_id,
        new_quick_status,
    )
    return CompanyApplicationRepository(
        request.state.request_scope
    ).get_company_view_single(application_id)


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
    # AJBTODO Move this to unit of work and make recruiter update async??
    ApplicationRepository(request.state.request_scope).update_fields(
        application_id, application_status=new_status.status.value
    )
    mixpanel.application_status_is_updated(
        request.state.request_scope.user_id,
        company_id,
        job_id,
        application_id,
        new_status.status.value,
    )
    RecruiterUpdatesRepository(
        request.state.request_scope, application_id
    ).update_application_status(
        company_id,
        job_id,
        application_id,
        request.state.request_scope.user_id,
        new_status.status,
        new_status.update_reason,
    )
    return CompanyApplicationRepository(
        request.state.request_scope
    ).get_company_view_single(application_id)


@router.patch("/jobs/{job_id}/applications/{application_id}/view")
def view_applications(request: Request, company_id: str, application_ids: list[str]):
    response = ApplicationUseCase(
        request.state.request_scope
    ).company_views_applications(company_id, application_ids)
    for application_id in application_ids:
        mixpanel.application_is_viewed(
            request.state.request_scope.user_id, company_id, None, application_id
        )
    return response
