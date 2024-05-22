from fastapi import APIRouter, Request, Depends

from ajb.base import QueryFilterParams, build_pagination_response
from ajb.contexts.companies.invitations.models import (
    UserCreateInvitation,
    InvitationPaginatedResponse,
    Invitation,
)
from ajb.contexts.companies.invitations.usecase import CompanyInvitationUseCase
from ajb.contexts.companies.invitations.repository import InvitationRepository
from ajb.exceptions import RecruiterCreateException

from api.exceptions import GenericHTTPException
from api.middleware import scope


router = APIRouter(tags=["Company Invitations"])


@router.get(
    "/companies/{company_id}/invitations", response_model=InvitationPaginatedResponse
)
def get_company_invitations(
    request: Request, company_id: str, query: QueryFilterParams = Depends()
):
    """Gets all invitations for a company"""
    response = InvitationRepository(
        scope(request), company_id
    ).get_all_invitations_for_company()
    return build_pagination_response(
        response,
        query.page,
        query.page_size,
        request.url._url,
        InvitationPaginatedResponse,
    )


@router.post("/companies/{company_id}/invitations", response_model=Invitation)
def create_invitation(request: Request, company_id: str, data: UserCreateInvitation):
    """Creates an invitation for a company"""
    try:
        response = CompanyInvitationUseCase(scope(request)).user_creates_invite(
            data, scope(request).user_id, company_id
        )
        return response
    except RecruiterCreateException as e:
        raise GenericHTTPException(400, str(e))


@router.delete("/companies/{company_id}/invitations/{invitation_id}")
def cancel_invitation(request: Request, company_id: str, invitation_id: str):
    """Cancels an invitation for a company"""
    return CompanyInvitationUseCase(scope(request)).user_cancels_invitation(
        company_id, invitation_id, scope(request).user_id
    )


@router.post("/confirm-recruiter-invitation")
def confirm_invitation(request: Request, encoded_invitation: str):
    """Assumes user is logged in and accepts invitation"""
    return CompanyInvitationUseCase(scope(request)).user_confirms_invitations(
        scope(request).user_id, encoded_invitation
    )
