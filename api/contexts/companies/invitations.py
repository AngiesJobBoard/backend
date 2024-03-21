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

from api.vendors import mixpanel
from api.exceptions import GenericHTTPException


router = APIRouter(tags=["Company Invitations"])


@router.get(
    "/companies/{company_id}/invitations", response_model=InvitationPaginatedResponse
)
def get_company_invitations(
    request: Request, company_id: str, query: QueryFilterParams = Depends()
):
    """Gets all invitations for a company"""
    response = InvitationRepository(
        request.state.request_scope, company_id
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
        response = CompanyInvitationUseCase(
            request.state.request_scope
        ).user_creates_invite(data, request.state.request_scope.user_id, company_id)
        mixpanel.recruiter_is_invited_to_company(
            request.state.request_scope.user_id,
            company_id,
            data.role.value,
            response.id,
        )
        return response
    except RecruiterCreateException as e:
        raise GenericHTTPException(400, str(e))


@router.delete("/companies/{company_id}/invitations/{invitation_id}")
def cancel_invitation(request: Request, company_id: str, invitation_id: str):
    """Cancels an invitation for a company"""
    return CompanyInvitationUseCase(
        request.state.request_scope
    ).user_cancels_invitation(
        company_id, invitation_id, request.state.request_scope.user_id
    )


@router.post("/confirm-recruiter-invitation")
def confirm_invitation(request: Request, encoded_invitation: str):
    """Assumes user is logged in and accepts invitation"""
    response = CompanyInvitationUseCase(
        request.state.request_scope
    ).user_confirms_invitations(request.state.request_scope.user_id, encoded_invitation)
    mixpanel.recruiter_invitation_is_accepted(
        request.state.request_scope.user_id,
        response.company_id,
        response.role.value,
        response.id,
    )
    return response
