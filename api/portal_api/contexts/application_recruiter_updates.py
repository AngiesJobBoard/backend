from fastapi import (
    APIRouter,
    Request,
    Depends,
)
from ajb.base import build_pagination_response
from ajb.contexts.applications.recruiter_updates.repository import (
    RecruiterUpdatesRepository,
)
from ajb.contexts.applications.recruiter_updates.usecase import RecruiterUpdatesUseCase
from ajb.contexts.applications.recruiter_updates.models import (
    ApplicationUpdate,
    PaginatedCompanyUpdateView,
    ApplicationUpdateQuery,
    UserCreateRecruiterComment,
)
from api.middleware import scope

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
    results = RecruiterUpdatesUseCase(scope(request)).get_application_update_timeline(
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
    return RecruiterUpdatesUseCase(scope(request)).add_recruiter_comment(
        company_id,
        job_id,
        application_id,
        scope(request).user_id,
        recruiter_comment.comment,
    )


@router.delete("/jobs/{job_id}/applications/{application_id}/updates/{update_id}")
def delete_recruiter_update(
    request: Request,
    application_id: str,
    update_id: str,
):
    """Deletes a recruiter comment"""
    return RecruiterUpdatesRepository(scope(request), application_id).delete(update_id)


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
    return RecruiterUpdatesRepository(scope(request), application_id).update_fields(
        comment_id,
        comment=recruiter_comment.comment,
    )
