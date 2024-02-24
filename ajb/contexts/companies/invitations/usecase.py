from typing import cast

from ajb.base import BaseUseCase, Collection
from ajb.contexts.companies.recruiters.models import Recruiter, CreateRecruiter
from ajb.contexts.users.models import User
from ajb.contexts.companies.recruiters.repository import (
    RecruiterRepository,
    RecruiterAndUser,
)
from ajb.config.settings import SETTINGS
from ajb.exceptions import (
    GenericPermissionError,
    RecruiterCreateException,
    EntityNotFound,
)
from ajb.vendor.jwt import decode_jwt
from ajb.vendor.sendgrid.repository import SendgridRepository
from ajb.vendor.sendgrid.templates.company_invitation.models import CompanyInvitation

from .models import UserCreateInvitation, CreateInvitation, Invitation, InvitationData
from ..models import RecruiterRole


class CompanyInvitationUseCase(BaseUseCase):
    def user_creates_invite(
        self, data: UserCreateInvitation, inviting_user_id: str, company_id: str
    ) -> Invitation:
        with self.request_scope.start_transaction(
            read_collections=[Collection.RECRUITER_INVITATIONS, Collection.COMPANIES],
            write_collections=[Collection.RECRUITER_INVITATIONS],
        ) as transaction_scope:
            invitation_repo = self.get_repository(
                Collection.RECRUITER_INVITATIONS, transaction_scope, company_id
            )

            created_invitation = invitation_repo.create(
                CreateInvitation(
                    inviting_user_id=inviting_user_id,
                    email_address=data.email_address,
                    company_id=company_id,
                    role=data.role,
                )
            )

            company_name = (
                self.get_repository(Collection.COMPANIES, transaction_scope)
                .get(company_id)
                .name
            )

            # Send email notification with encoded invitation
            invitation_data = InvitationData(
                email_address=data.email_address,
                invitation_id=created_invitation.id,
                company_id=company_id,
            )
            deeplink_param = invitation_data.convert_to_deeplink_param(
                SETTINGS.RECRUITER_INVITATION_SECRET
            )
            invitation_link = (
                f"{SETTINGS.APP_URL}/confirm-invite?invite={deeplink_param}"
            )
            SendgridRepository().send_rendered_email_template(
                to_emails=data.email_address,
                subject="You've been invited to Angie's Job Board!",
                template_name="company_invitation",
                template_data=CompanyInvitation(
                    companyName=company_name,
                    invitationLink=invitation_link,
                ),
            )
            return created_invitation

    def user_confirms_invitations(
        self, accepting_user_id: str, deeplink_param: str
    ) -> RecruiterAndUser:
        with self.request_scope.start_transaction(
            read_collections=[Collection.RECRUITER_INVITATIONS],
            write_collections=[
                Collection.RECRUITER_INVITATIONS,
                Collection.COMPANY_RECRUITERS,
            ],
        ) as transaction_scope:
            decoded_invitation = InvitationData(
                **decode_jwt(deeplink_param, SETTINGS.RECRUITER_INVITATION_SECRET)
            )

            # Check that the accepting user exists and is the same as the invited user
            user_repo = self.get_repository(Collection.USERS, transaction_scope)
            try:
                accepting_user: User = user_repo.get(accepting_user_id)
            except EntityNotFound:
                raise RecruiterCreateException("Accepting user does not exist")

            # if accepting_user.email != decoded_invitation.email_address:
            #     raise RecruiterCreateException(
            #         "Invitation email does not match accepting user email"
            #     )

            # Check invitation exists and company id matches
            try:
                invitation_repo = self.get_repository(
                    Collection.RECRUITER_INVITATIONS,
                    transaction_scope,
                    decoded_invitation.company_id,
                )
                invitation: Invitation = invitation_repo.get(
                    decoded_invitation.invitation_id
                )
            except EntityNotFound:
                raise RecruiterCreateException("Invitation does not exist")

            # If exists, delete invitation and create recruiter
            recruiter_repo = self.get_repository(
                Collection.COMPANY_RECRUITERS,
                transaction_scope,
                decoded_invitation.company_id,
            )
            recruiter_repo = cast(RecruiterRepository, recruiter_repo)
            created_recruiter = recruiter_repo.create(
                CreateRecruiter(
                    user_id=accepting_user_id,
                    company_id=decoded_invitation.company_id,
                    role=invitation.role,
                )
            )
            invitation_repo.delete(decoded_invitation.invitation_id)
            recruiter_and_user = recruiter_repo.get_recruiter_by_id(
                created_recruiter.id
            )

            # Clean up all other invitations for this user and company
            all_other_invitations: list[Invitation] = invitation_repo.query(
                company_id=decoded_invitation.company_id,
                email_address=decoded_invitation.email_address,
            )[0]
            invitation_repo.delete_many(
                [invitation.id for invitation in all_other_invitations]
            )

        return recruiter_and_user

    def user_cancels_invitation(
        self, company_id: str, invitation_id: str, cancelling_user_id: str
    ) -> bool:
        # Check user is admin or owner on company
        recruiter_repo = self.get_repository(
            Collection.COMPANY_RECRUITERS, self.request_scope, company_id
        )
        user: Recruiter = recruiter_repo.get_one(user_id=cancelling_user_id)
        if user.role not in [RecruiterRole.ADMIN, RecruiterRole.OWNER]:
            raise GenericPermissionError

        invitation_repo = self.get_repository(
            Collection.RECRUITER_INVITATIONS, self.request_scope, company_id
        )
        return invitation_repo.delete(invitation_id)
