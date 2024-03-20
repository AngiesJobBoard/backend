from fastapi import (
    APIRouter,
    Request,
    Depends,
)

from ajb.base import QueryFilterParams, RepoFilterParams, build_pagination_response
from ajb.contexts.applications.models import (
    CompanyApplicationView,
    PaginatedCompanyApplicationView,
    UserCreateRecruiterNote,
    CreateRecruiterNote,
    CreateApplicationStatusUpdate,
    ApplicationStatusRecord,
)
from ajb.contexts.applications.repository import (
    CompanyApplicationRepository,
    ApplicationRepository,
)
from ajb.contexts.applications.usecase import ApplicationUseCase
from ajb.vendor.arango.models import Filter, Operator


router = APIRouter(
    tags=["Company Applications"], prefix="/companies/{company_id}/applications"
)


@router.get("/", response_model=PaginatedCompanyApplicationView)
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
        PaginatedCompanyApplicationView,
    )


@router.post("/many", response_model=PaginatedCompanyApplicationView)
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
        PaginatedCompanyApplicationView,
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
    application = ApplicationRepository(request.state.request_scope).get(application_id)
    assert application.company_id == company_id
    return ApplicationUseCase(request.state.request_scope).delete_application_for_job(
        application.company_id, application.job_id, application.id
    )


@router.patch("/{application_id}/add-shortlist")
def add_application_to_shortlist(
    request: Request, company_id: str, application_id: str
):
    return ApplicationUseCase(
        request.state.request_scope
    ).company_updates_application_shortlist(company_id, application_id, True)


@router.patch("/{application_id}/remove-shortlist")
def remove_application_to_shortlist(
    request: Request, company_id: str, application_id: str
):
    return ApplicationUseCase(
        request.state.request_scope
    ).company_updates_application_shortlist(company_id, application_id, False)


@router.patch("/{application_id}/view")
def view_applications(request: Request, company_id: str, application_ids: list[str]):
    return ApplicationUseCase(request.state.request_scope).company_views_applications(
        company_id, application_ids
    )


@router.post("/{application_id}/notes")
def create_recruiter_note(
    request: Request,
    company_id: str,
    application_id: str,
    new_note: UserCreateRecruiterNote,
):
    """Creates a recruiter note"""
    return CompanyApplicationRepository(
        request.state.request_scope
    ).create_recruiter_note(
        company_id,
        application_id,
        CreateRecruiterNote(
            note=new_note.note, user_id=request.state.request_scope.user_id
        ),
    )


@router.put("/{application_id}/notes/{note_id}")
def update_recruiter_note(
    request: Request,
    company_id: str,
    application_id: str,
    note_id: str,
    updated_note: UserCreateRecruiterNote,
):
    """Updates a recruiter note"""
    return CompanyApplicationRepository(
        request.state.request_scope
    ).update_recruiter_note(
        company_id,
        application_id,
        note_id,
        CreateRecruiterNote(
            note=updated_note.note, user_id=request.state.request_scope.user_id
        ),
    )


@router.delete("/{application_id}/notes/{note_id}")
def delete_recruiter_note(
    request: Request, company_id: str, application_id: str, note_id: str
):
    """Deletes a recruiter note"""
    return CompanyApplicationRepository(
        request.state.request_scope
    ).delete_recruiter_note(company_id, application_id, note_id)


@router.post("/{application_id}/status")
def update_application_status(
    request: Request,
    company_id: str,
    application_id: str,
    new_status: CreateApplicationStatusUpdate,
):
    """Updates an application status"""
    new_update = ApplicationStatusRecord(
        **new_status.model_dump(),
        updated_by_user_id=request.state.request_scope.user_id,
        update_made_by_admin=False
    )
    return CompanyApplicationRepository(
        request.state.request_scope
    ).update_application_status(company_id, application_id, new_update)
