from fastapi import APIRouter, Request

from ajb.vendor.clerk.models import SimpleClerkCreateUser
from ajb.contexts.users.usecase import UserUseCase
from ajb.contexts.users.models import User
from ajb.exceptions import AdminCreateUserException

from api.exceptions import GenericHTTPException


router = APIRouter(tags=["Admin Create Users"], prefix="/admin/create-users")


@router.post("/", response_model=User)
def admin_create_user(request: Request, user: SimpleClerkCreateUser):
    try:
        return UserUseCase(request.state.request_scope).admin_create_user(user)
    except AdminCreateUserException as exc:
        raise GenericHTTPException(
            status_code=500,
            detail=exc.message,
        )
