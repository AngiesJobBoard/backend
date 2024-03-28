import json
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ajb.contexts.users.repository import UserRepository
from ajb.contexts.users.models import UpdateUser, User
from ajb.contexts.companies.recruiters.repository import RecruiterRepository, Recruiter


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
    return UserRepository(request.state.request_scope).update(
        request.state.request_scope.user_id, user
    )


@router.get("/companies/{company_id}/recruiter", response_model=Recruiter)
def get_me_as_a_recruiter(request: Request, company_id: str):
    return RecruiterRepository(request.state.request_scope, company_id).get_one(
        user_id=request.state.request_scope.user_id, company_id=company_id
    )
