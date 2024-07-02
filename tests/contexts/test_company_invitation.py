import pytest
from ajb.contexts.companies.invitations.usecase import (
    CompanyInvitationUseCase,
    UserCreateInvitation,
    InvitationData,
)
from ajb.contexts.companies.recruiters.models import RecruiterRole
from ajb.contexts.companies.recruiters.repository import RecruiterRepository
from ajb.exceptions import RecruiterCreateException


from ajb.fixtures.companies import CompanyFixture
from ajb.fixtures.users import UserFixture


TEST_EMAIL = "nice@test.com"
INVITATION_NOT_EXIST = "Invitation does not exist"


def test_create_invitation(request_scope):
    usecase = CompanyInvitationUseCase(request_scope)
    user, company = CompanyFixture(request_scope).create_company_with_owner()

    usecase.user_creates_invite(
        UserCreateInvitation(
            email=TEST_EMAIL,
            role=RecruiterRole.ADMIN,
        ),
        inviting_user_id=user.id,
        company_id=company.id,
    )


def test_cancel_invitation(request_scope):
    usecase = CompanyInvitationUseCase(request_scope)
    user, company = CompanyFixture(request_scope).create_company_with_owner()

    usecase.user_creates_invite(
        UserCreateInvitation(
            email=TEST_EMAIL,
            role=RecruiterRole.ADMIN,
        ),
        inviting_user_id=user.id,
        company_id=company.id,
    )


def test_accept_invitation(request_scope):
    usecase = CompanyInvitationUseCase(request_scope)
    user, company = CompanyFixture(request_scope).create_company_with_owner()

    # Create new user to accept invitation
    new_user = UserFixture(request_scope).create_user(email=TEST_EMAIL)

    invitation = usecase.user_creates_invite(
        UserCreateInvitation(
            email=TEST_EMAIL,
            role=RecruiterRole.ADMIN,
        ),
        inviting_user_id=user.id,
        company_id=company.id,
    )

    # Recreate the invitation data to test acceptance
    invitation_data = InvitationData(
        email=invitation.email,
        invitation_id=invitation.id,
        company_id=invitation.company_id,
    )

    # All correct state
    created_recruiter = usecase.user_confirms_invitations(
        new_user.id, invitation_data.convert_to_deeplink_param("test")
    )

    # Check recruiter was created
    recruiter_repo = RecruiterRepository(request_scope, company.id)
    assert recruiter_repo.get(created_recruiter.id)

    # Same user can't accept twice
    with pytest.raises(RecruiterCreateException) as excinfo:
        usecase.user_confirms_invitations(
            new_user.id, invitation_data.convert_to_deeplink_param("test")
        )
    assert INVITATION_NOT_EXIST in str(excinfo.value)


def test_accept_invitation_failures(request_scope):
    usecase = CompanyInvitationUseCase(request_scope)
    user, company = CompanyFixture(request_scope).create_company_with_owner()

    # Create new user to accept invitation
    new_user = UserFixture(request_scope).create_user(email=TEST_EMAIL)

    invitation = usecase.user_creates_invite(
        UserCreateInvitation(
            email=TEST_EMAIL,
            role=RecruiterRole.ADMIN,
        ),
        inviting_user_id=user.id,
        company_id=company.id,
    )

    # Recreate the invitation data to test acceptance
    invitation_data = InvitationData(
        email=invitation.email,
        invitation_id=invitation.id,
        company_id=invitation.company_id,
    )

    # Make accepting user non existant
    with pytest.raises(RecruiterCreateException) as excinfo:
        usecase.user_confirms_invitations(
            "not_a_user", invitation_data.convert_to_deeplink_param("test")
        )
    assert "Accepting user does not exist" in str(excinfo.value)

    # Invitation doesn't exist
    with pytest.raises(RecruiterCreateException) as excinfo:
        bad_invidaton_data = invitation_data.model_copy(deep=True)
        bad_invidaton_data.invitation_id = "wrong"
        usecase.user_confirms_invitations(
            new_user.id, bad_invidaton_data.convert_to_deeplink_param("test")
        )
    assert INVITATION_NOT_EXIST in str(excinfo.value)

    # Invitation company doesn't match
    with pytest.raises(RecruiterCreateException) as excinfo:
        bad_invidaton_data = invitation_data.model_copy(deep=True)
        bad_invidaton_data.company_id = "wrong"
        usecase.user_confirms_invitations(
            new_user.id, bad_invidaton_data.convert_to_deeplink_param("test")
        )
    assert INVITATION_NOT_EXIST in str(excinfo.value)
