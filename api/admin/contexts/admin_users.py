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
from api.middleware import scope

router = APIRouter(tags=["Admin Users"], prefix="/admin-users")


@router.get("/", response_model=AdminAndUserPaginatedResponse)
def get_all_admin_users(request: Request, query: QueryFilterParams = Depends()):
    results = AdminUserRepository(scope(request)).get_admin_and_user(query)
    return build_pagination_response(
        results,
        query.page,
        query.page_size,
        request.url._url,
        AdminAndUserPaginatedResponse,
    )


@router.get("/{id}", response_model=AdminUser)
def get_admin_user_by_id(id: str, request: Request):
    return AdminUserRepository(scope(request)).get(id)


@router.post("/", response_model=AdminUser)
def create_admin_user(request: Request, admin_user: UserCreateAdminUser):
    return AdminUserUseCase(scope(request)).create_admin(admin_user)


@router.put("/{id}", response_model=AdminUser)
def update_user_role(id: str, request: Request, role: AdminRoles):
    return AdminUserRepository(scope(request)).update_fields(id, role=role)


@router.delete("/{id}")
def delete_admin_user(id: str, request: Request):
    return AdminUserRepository(scope(request)).delete(id)
