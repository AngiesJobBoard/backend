from fastapi import (
    APIRouter,
    Request,
    Depends,
)
from ajb.base import build_pagination_response
from ajb.contexts.applications.recruiter_updates.repository import (
    RecruiterUpdatesRepository,
)
from ajb.contexts.applications.recruiter_updates.models import (
    ApplicationUpdate,
    PaginatedCompanyUpdateView,
    ApplicationUpdateQuery,
    UserCreateRecruiterComment,
)
from ajb.contexts.applications.repository import ApplicationRepository
from ajb.contexts.applications.models import (
    CreateApplicationStatusUpdate,
)
from ajb.contexts.applications.usecase import ApplicationUseCase

from api.vendors import mixpanel


router = APIRouter(
    tags=["Company Application Updates"],
    prefix="/companies/{company_id}",
)


@router.get("/application-updates", response_model=PaginatedCompanyUpdateView)
def get_all_recruiter_updates(
    request: Request,
    update_query: ApplicationUpdateQuery = Depends(),
):
    """Gets all recruiter updates for a given company"""
    results = RecruiterUpdatesRepository(
        request.state.request_scope
    ).get_application_update_timeline(
        update_query.company_id,
        update_query.job_id,
        update_query.application_id,
        update_query.start_date,
        update_query.end_date,
        update_query.page,
        update_query.page_size,
    )
    return build_pagination_response(
        results,
        update_query.page,
        update_query.page_size,
        request.url._url,
        PaginatedCompanyUpdateView,
    )


@router.post(
    "/jobs/{job_id}/applications/{application_id}/updates",
    response_model=ApplicationUpdate,
)
def create_recruiter_comment(
    request: Request,
    company_id: str,
    job_id: str,
    application_id: str,
    recruiter_comment: UserCreateRecruiterComment,
):
    """Creates a recruiter comment"""
    return RecruiterUpdatesRepository(
        request.state.request_scope, application_id
    ).add_recruiter_comment(
        company_id,
        job_id,
        application_id,
        request.state.request_scope.user_id,
        recruiter_comment.comment,
    )


@router.delete("/jobs/{job_id}/applications/{application_id}/updates/{update_id}")
def delete_recruiter_update(
    request: Request,
    application_id: str,
    update_id: str,
):
    """Deletes a recruiter comment"""
    return RecruiterUpdatesRepository(
        request.state.request_scope, application_id
    ).delete(update_id)


@router.patch(
    "/jobs/{job_id}/applications/{application_id}/updates/{update_id}",
    response_model=ApplicationUpdate,
)
def update_recruiter_comment(
    request: Request,
    application_id: str,
    comment_id: str,
    recruiter_comment: UserCreateRecruiterComment,
):
    """Updates a recruiter comment"""
    return RecruiterUpdatesRepository(
        request.state.request_scope, application_id
    ).update_fields(
        comment_id,
        comment=recruiter_comment.comment,
    )


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


@router.post("/jobs/{job_id}/applications/{application_id}/status")
def update_application_status(
    request: Request,
    company_id: str,
    job_id: str,
    application_id: str,
    new_status: CreateApplicationStatusUpdate,
):
    """Updates an application status"""
    response = ApplicationRepository(
        request.state.request_scope
    ).update_fields(application_id, application_status=new_status)
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
    return response


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
