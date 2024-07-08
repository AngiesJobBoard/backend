from fastapi import APIRouter, Depends, Request

from api.app.contexts import (
    enumerations,
    health,
    static_data,
    users,
)
from api.app.contexts.companies.app import company_api_router
from ajb.contexts.companies.invitations.usecase import CompanyInvitationUseCase
from api.app.middleware import verify_user
from api.middleware import scope

portal_api_router = APIRouter()

portal_api_router.include_router(company_api_router)
portal_api_router.include_router(enumerations.router, dependencies=[Depends(verify_user)])
portal_api_router.include_router(health.router)
portal_api_router.include_router(static_data.router, dependencies=[Depends(verify_user)])
portal_api_router.include_router(users.router, dependencies=[Depends(verify_user)])


@portal_api_router.post("/confirm-recruiter-invitation")
def confirm_invitation(request: Request, encoded_invitation: str):
    """Assumes user is logged in and accepts invitation"""
    return CompanyInvitationUseCase(scope(request)).user_confirms_invitations(
        scope(request).user_id, encoded_invitation
    )
