from fastapi import APIRouter, Request, Depends

from ajb.base import QueryFilterParams, build_pagination_response
from ajb.contexts.admin.users.models import (
    AdminUser,
    UserCreateAdminUser,
    AdminRoles,
)
from ajb.contexts.admin.users.repository import AdminUserRepository
from ajb.contexts.admin.users.usecase import AdminUserUseCase
from ajb.contexts.admin.users.models import AdminAndUserPaginatedResponse

router = APIRouter(tags=["Admin Users"], prefix="/admin/admin-users")


@router.get("/", response_model=AdminAndUserPaginatedResponse)
def get_all_admin_users(request: Request, query: QueryFilterParams = Depends()):
    results = AdminUserRepository(request.state.request_scope).get_admin_and_user(query)
    return build_pagination_response(
        results,
        query.page,
        query.page_size,
        request.url._url,
        AdminAndUserPaginatedResponse,
    )


@router.get("/autocomplete")
def get_admin_user_autocomplete(request: Request, prefix: str, field: str = "email"):
    return AdminUserRepository(request.state.request_scope).get_autocomplete(
        field, prefix
    )


@router.get("/{id}", response_model=AdminUser)
def get_admin_user_by_id(id: str, request: Request):
    return AdminUserRepository(request.state.request_scope).get(id)


@router.post("/", response_model=AdminUser)
def create_admin_user(request: Request, admin_user: UserCreateAdminUser):
    return AdminUserUseCase(request.state.request_scope).create_admin(admin_user)


@router.put("/{id}", response_model=AdminUser)
def update_user_role(id: str, request: Request, role: AdminRoles):
    return AdminUserRepository(request.state.request_scope).update_fields(id, role=role)


@router.delete("/{id}")
def delete_admin_user(id: str, request: Request):
    return AdminUserRepository(request.state.request_scope).delete(id)
