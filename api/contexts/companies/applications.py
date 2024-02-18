from fastapi import (
    APIRouter,
    Request,
    Depends,
)

from ajb.base import QueryFilterParams, build_pagination_response
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


router = APIRouter(
    tags=["Company Applications"], prefix="/companies/{company_id}/applications"
)


@router.get("/", response_model=PaginatedCompanyApplicationView)
def get_all_company_applications(
    request: Request,
    company_id: str,
    query: QueryFilterParams = Depends(),
    shortlist_only: bool = False,
):
    """Gets all applications"""
    results = CompanyApplicationRepository(
        request.state.request_scope
    ).get_company_view_list(company_id, query, shortlist_only)
    return build_pagination_response(
        results,
        query.page,
        query.page_size,
        request.url._url,
        PaginatedCompanyApplicationView,
    )


@router.get("/{application_id}", response_model=CompanyApplicationView)
def get_company_application(request: Request, company_id: str, application_id: str):
    """Gets a single application"""
    return CompanyApplicationRepository(
        request.state.request_scope
    ).get_company_view_single(company_id, application_id)


@router.delete("/{application_id}")
def delete_company_application(request: Request, company_id: str, application_id: str):
    """Deletes an application"""
    # First make sure that the application exists for this company
    application = ApplicationRepository(request.state.request_scope).get(application_id)
    assert application.company_id == company_id
    return ApplicationRepository(request.state.request_scope).delete(application_id)


@router.patch("/{application_id}/add-shortlist")
def add_application_to_shortlist(
    request: Request, company_id: str, application_id: str
):
    return CompanyApplicationRepository(
        request.state.request_scope
    ).company_updates_application_shortlist(company_id, application_id, True)


@router.patch("/{application_id}/remove-shortlist")
def remove_application_to_shortlist(
    request: Request, company_id: str, application_id: str
):
    return CompanyApplicationRepository(
        request.state.request_scope
    ).company_updates_application_shortlist(company_id, application_id, False)


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
