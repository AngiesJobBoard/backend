"""
This module is for various admin capabilities which can be organized better llllaaattteeerrr
"""

from fastapi import APIRouter, Request, Depends

from ajb.contexts.companies.recruiters.repository import RecruiterRepository
from ajb.contexts.companies.recruiters.models import (
    UserCreateRecruiter,
    CreateRecruiter,
    Recruiter,
)


router = APIRouter(tags=["Admin Etc."], prefix="/admin/etc")


@router.post("/add-user-to-company", response_model=Recruiter)
def add_user_to_company(request: Request, payload: UserCreateRecruiter):
    return RecruiterRepository(request_scope=request.state.request_scope).create(
        CreateRecruiter(**payload.model_dump())
    )
