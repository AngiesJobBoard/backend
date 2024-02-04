import json
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ajb.contexts.users.repository import UserRepository
from ajb.contexts.users.models import UpdateUser, User
from ajb.contexts.users.usecase import UserUseCase


router = APIRouter(tags=["Users"], prefix="/me")


@router.get("/state")
def get_current_user_state(request: Request):
    return JSONResponse(
        json.loads(
            json.dumps(
                {
                    "state": request.state.user.dict(),
                    "companies": request.state.companies,
                },
                default=str,
            )
        )
    )


@router.get("/", response_model=User)
def get_current_user(request: Request):
    return UserRepository(request.state.request_scope).get(
        request.state.request_scope.user_id
    )


@router.patch("/", response_model=User)
def update_current_user(request: Request, user: UpdateUser):
    return UserUseCase(request.state.request_scope).update_user(
        request.state.request_scope.user_id, user
    )


@router.post("/publish-profile")
def post_candidate(request: Request):
    return UserUseCase(request.state.request_scope).make_user_information_public(
        request.state.request_scope.user_id
    )


@router.post("/unpublish-profile")
def unpost_candidate(request: Request):
    return UserUseCase(request.state.request_scope).make_user_information_private(
        request.state.request_scope.user_id
    )
