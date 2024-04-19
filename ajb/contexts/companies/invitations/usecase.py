from typing import cast

from ajb.base import BaseUseCase, Collection
from ajb.contexts.companies.recruiters.models import CreateRecruiter
from ajb.contexts.companies.recruiters.repository import (
    RecruiterRepository,
    RecruiterAndUser,
)
from ajb.contexts.billing.usecase import CompanyBillingUsecase, UsageType
from ajb.config.settings import SETTINGS
from ajb.exceptions import (
    RecruiterCreateException,
    EntityNotFound,
)
from ajb.vendor.jwt import decode_jwt
from ajb.vendor.sendgrid.repository import SendgridRepository
from ajb.vendor.sendgrid.templates.recruiter_invitation import RecruiterInvitationData

from .models import UserCreateInvitation, CreateInvitation, Invitation, InvitationData


class EmailAlreadyExistsException(Exception):
    pass


class CompanyInvitationUseCase(BaseUseCase):
    def user_creates_invite(
        self, data: UserCreateInvitation, inviting_user_id: str, company_id: str
    ) -> Invitation:
        with self.request_scope.start_transaction(
            read_collections=[Collection.RECRUITER_INVITATIONS, Collection.COMPANIES],
            write_collections=[Collection.RECRUITER_INVITATIONS],
        ) as transaction_scope:
            user_repo = self.get_repository(Collection.USERS, transaction_scope)
            recruiter_repo = self.get_repository(
                Collection.COMPANY_RECRUITERS, transaction_scope, company_id
            )
            invitation_repo = self.get_repository(
                Collection.RECRUITER_INVITATIONS, transaction_scope, company_id
            )
            # First check if email exists as user already and if that user is already a recruiter - then abort
            potential_user = user_repo.get_all(email=data.email)
            if potential_user:
                potential_recruiter = recruiter_repo.get_all(
                    user_id=potential_user[0].id, company_id=company_id
                )
                if potential_recruiter:
                    raise EmailAlreadyExistsException

            # If there are any matches of same companyID and email then update the invitation
            potential_application = invitation_repo.get_all(
                company_id=company_id, email=data.email
            )
            if not potential_application:
                created_invitation = invitation_repo.create(
                    CreateInvitation(
                        inviting_user_id=inviting_user_id,
                        email=data.email,
                        company_id=company_id,
                        role=data.role,
                    )
                )
            else:
                created_invitation = invitation_repo.update_fields(
                    potential_application[0].id, role=data.role
                )

            company_name = (
                self.get_repository(Collection.COMPANIES, transaction_scope)
                .get(company_id)
                .name
            )

            # Send email notification with encoded invitation
            invitation_data = InvitationData(
                email=data.email,
                invitation_id=created_invitation.id,
                company_id=company_id,
            )
            deeplink_param = invitation_data.convert_to_deeplink_param(
                SETTINGS.RECRUITER_INVITATION_SECRET
            )
            invitation_link = (
                f"{SETTINGS.APP_URL}/confirm-invite?invite={deeplink_param}"
            )
            SendgridRepository().send_email_template(
                to_emails=data.email,
                subject="You've been invited to Angie's Job Board!",
                template_data=RecruiterInvitationData(
                    companyName=company_name,
                    platformName=SETTINGS.APP_NAME,
                    invitationLink=invitation_link,
                    supportEmail=SETTINGS.SUPPORT_EMAIL,
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
                user_repo.get(accepting_user_id)
            except EntityNotFound:
                raise RecruiterCreateException("Accepting user does not exist")

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
                email=decoded_invitation.email,
            )[0]
            invitation_repo.delete_many(
                [invitation.id for invitation in all_other_invitations]
            )

        CompanyBillingUsecase(self.request_scope).increment_company_usage(
            company_id=decoded_invitation.company_id,
            incremental_usages={
                UsageType.TOTAL_RECRUITERS: 1,
            },
        )
        return recruiter_and_user

    def user_cancels_invitation(
        self, company_id: str, invitation_id: str, cancelling_user_id: str
    ) -> bool:
        invitation_repo = self.get_repository(
            Collection.RECRUITER_INVITATIONS, self.request_scope, company_id
        )
        return invitation_repo.delete(invitation_id)
