from fastapi import APIRouter, Request, Depends

from ajb.base import QueryFilterParams, build_pagination_response
from ajb.contexts.applications.models import (
    UserCreatedApplication,
    Application,
    UserApplicationView,
    PaginatedUserApplicationView,
)
from ajb.contexts.applications.repository import UserApplicationRepository
from ajb.contexts.applications.usecase import ApplicationsUseCase


router = APIRouter(tags=["User Applications"], prefix="/applications")


@router.get("/", response_model=PaginatedUserApplicationView)
def get_all_user_applications(request: Request, query: QueryFilterParams = Depends()):
    """Gets all applications"""
    results = UserApplicationRepository(
        request.state.request_scope
    ).get_candidate_view_list(request.state.request_scope.user_id, query=query)
    return build_pagination_response(
        results,
        query.page,
        query.page_size,
        request.url._url,
        PaginatedUserApplicationView,
    )


@router.get("/{application_id}", response_model=UserApplicationView)
def get_user_application(request: Request, application_id: str):
    """Gets a single application"""
    return UserApplicationRepository(
        request.state.request_scope
    ).get_candidate_view_single(request.state.request_scope.user_id, application_id)


@router.post("/", response_model=Application)
def create_application(request: Request, application: UserCreatedApplication):
    """Creates an application"""
    return ApplicationsUseCase(request.state.request_scope).user_creates_application(
        request.state.request_scope.user_id, application
    )


# @router.patch("/{application_id}")
# def user_updates_application(request: Request, application_id: str, update: USER_UPDATE):
#     """Updates an application"""
#     return UserApplicationRepository(request.state.request_scope).candidate_updates_application(
#         request.state.request_scope.user_id, application_id, update
#     )
