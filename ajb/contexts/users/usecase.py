from ajb.base import BaseUseCase, Collection, RequestScope
from ajb.contexts.users.models import User, UserProfileUpload
from ajb.vendor.clerk.models import SimpleClerkCreateUser, ClerkCreateUser
from ajb.vendor.clerk.repository import ClerkAPIRepository
from ajb.contexts.webhooks.ingress.users.usecase import (
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
from ajb.vendor.firebase_storage.repository import FirebaseStorageRepository
from ajb.utils import random_salt
from ajb.exceptions import AdminCreateUserException, RepositoryNotProvided

from .models import User


class UserUseCase(BaseUseCase):
    def __init__(
        self,
        request_scope: RequestScope,
        storage: FirebaseStorageRepository | None = None,
    ):
        self.request_scope = request_scope
        self.storage_repo = storage

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
            internal_creation=True,
        )
        if not isinstance(response, User):
            raise AdminCreateUserException
        return response

    def admin_ban_user(self, user_id: str, is_banned: bool) -> bool:
        clerk_repo = ClerkAPIRepository()
        if is_banned:
            return clerk_repo.ban_user(user_id)
        return clerk_repo.unban_user(user_id)

    def get_actor_token(self, user_id: str):
        clerk_repo = ClerkAPIRepository()
        return clerk_repo.create_actor_token(self.request_scope.user_id, user_id)

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

    def _create_profile_picture_path(self, user_id: str, file_type: str) -> str:
        return f"users/{user_id}/profile_picture-{random_salt()}.{file_type}"

    def update_profile_picture(self, data: UserProfileUpload):
        if not self.storage_repo:
            raise RepositoryNotProvided("Storage")

        user_repo = self.get_repository(Collection.USERS, self.request_scope)
        remote_file_path = self._create_profile_picture_path(
            data.user_id, data.file_type
        )
        profile_pic_url = self.storage_repo.upload_bytes(
            data.profile_picture_data, data.file_type, remote_file_path, True
        )
        return user_repo.update_fields(data.user_id, image_url=profile_pic_url)

    def verify_password(self, user_id: str, password: str) -> bool:
        clerk_repo = ClerkAPIRepository()
        try:
            return clerk_repo.verify_user_password(user_id, password)
        except Exception:
            return False

    def change_password(self, user_id: str, new_password: str):
        clerk_repo = ClerkAPIRepository()
        return clerk_repo.update_user_password(user_id, new_password)

    def change_email(self, user_id: str, new_email: str) -> bool:
        clerk_repo = ClerkAPIRepository()
        clerk_success = clerk_repo.set_and_verify_new_email_address(user_id, new_email)
        if clerk_success:
            user_repo = self.get_repository(Collection.USERS)
            user_repo.update_fields(user_id, email=new_email)
        return True
