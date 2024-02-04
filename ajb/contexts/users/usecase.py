from ajb.base import BaseUseCase, RequestScope, Collection
from ajb.contexts.users.models import User
from ajb.vendor.clerk.models import SimpleClerkCreateUser, ClerkCreateUser
from ajb.vendor.clerk.repository import ClerkAPIRepository
from ajb.contexts.webhooks.users.usecase import (
    WebhookUserUseCase,
    ClerkUserWebhookEvent,
    ClerkUserWebhookType,
    ClerkUser,
)
from ajb.exceptions import AdminCreateUserException
from ajb.vendor.algolia.repository import AlgoliaSearchRepository, AlgoliaIndex

from .models import User, UpdateUser, AlgoliaCandidateSearch


class UserUseCase(BaseUseCase):
    def __init__(
        self,
        request_scope: RequestScope,
        algolia_users: AlgoliaSearchRepository | None = None,
    ):
        self.request_scope = request_scope
        self.algolia_users = algolia_users or AlgoliaSearchRepository(
            AlgoliaIndex.CANDIDATES
        )

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

    def make_user_information_public(self, user_id: str):
        user = self.get_repository(Collection.USERS).update_fields(
            user_id, profile_is_public=True
        )
        self.algolia_users.create_object(
            user.id, AlgoliaCandidateSearch.convert_from_user(user).model_dump()
        )

    def make_user_information_private(self, user_id: str):
        self.get_repository(Collection.USERS).update_fields(
            user_id, profile_is_public=False
        )
        self.algolia_users.delete_object(user_id)

    def update_user(self, user_id: str, updates: UpdateUser) -> User:
        user_repo = self.get_repository(Collection.USERS)
        updated_user: User = user_repo.update(user_id, updates)
        updated_user = user_repo.update_fields(
            user_id, candidate_score=updated_user.get_candidate_score()
        )
        self.algolia_users.update_object(
            user_id, AlgoliaCandidateSearch.convert_from_user(updated_user).model_dump()
        )
        return updated_user
