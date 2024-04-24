from fastapi import APIRouter, Request, Body

from ajb.vendor.clerk.models import SimpleClerkCreateUser, SignInToken
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


@router.post("/ban", response_model=bool)
def ban_user(request: Request, user_id: str = Body(...), is_banned: bool = Body(...)):
    return UserUseCase(request.state.request_scope).admin_ban_user(user_id, is_banned)


@router.post("/actor_token", response_model=SignInToken)
def get_user_actor_token(request: Request, user_id: str = Body(...)):
    return UserUseCase(request.state.request_scope).get_actor_token(user_id)
