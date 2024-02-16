from ajb.base import BaseUseCase, Collection
from ajb.contexts.users.models import User
from ajb.vendor.clerk.models import SimpleClerkCreateUser, ClerkCreateUser
from ajb.vendor.clerk.repository import ClerkAPIRepository
from ajb.contexts.webhooks.users.usecase import (
    WebhookUserUseCase,
    ClerkUserWebhookEvent,
    ClerkUserWebhookType,
    ClerkUser,
)
from ajb.contexts.companies.recruiters.models import (
    CreateRecruiter,
    RecruiterRole,
    Recruiter,
)
from ajb.exceptions import AdminCreateUserException

from .models import User


class UserUseCase(BaseUseCase):
    def admin_create_user(
        self, new_user: SimpleClerkCreateUser, force_if_exists: bool = False
    ) -> User:
        # Check if email address is taken
        clerk_repo = ClerkAPIRepository()
        potential_user: ClerkUser | None = clerk_repo.get_user_by_email(new_user.email_address)  # type: ignore
        if potential_user and not force_if_exists:
            raise AdminCreateUserException
        if potential_user:
            print("User already exists in clerk, creating in database")
            created_clerk_user = potential_user
        else:
            created_clerk_user = clerk_repo.create_user(
                ClerkCreateUser(
                    first_name=new_user.first_name,
                    last_name=new_user.last_name,
                    email_address=[new_user.email_address],
                    password=new_user.password,
                    skip_password_checks=new_user.skip_password_checks,
                    skip_password_requirement=new_user.skip_password_requirement,
                    private_metadata={"created_by_admin": "true"},
                )
            )
        response: User | bool = WebhookUserUseCase(self.request_scope).create_user(
            ClerkUserWebhookEvent(
                data=created_clerk_user.model_dump(),
                object="user",
                type=ClerkUserWebhookType.user_created,
            ),
            return_user=True,
            internal_creation=True,
        )
        if not isinstance(response, User):
            raise AdminCreateUserException
        return response

    def admin_adds_user_to_company(
        self, user_id: str, company_id: str, role: RecruiterRole
    ) -> Recruiter:
        recruiter_repo = self.get_repository(
            Collection.COMPANY_RECRUITERS, self.request_scope, company_id
        )
        return recruiter_repo.create(
            CreateRecruiter(
                role=role,
                user_id=user_id,
                company_id=company_id,
            )
        )
