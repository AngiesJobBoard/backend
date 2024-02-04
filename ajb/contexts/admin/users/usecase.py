from typing import cast
from ajb.base import Collection, BaseUseCase
from ajb.contexts.users.repository import UserRepository
from ajb.exceptions import EntityNotFound

from .models import UserCreateAdminUser, CreateAdminUser


class AdminUserUseCase(BaseUseCase):
    def create_admin(self, new_user: UserCreateAdminUser):
        user_repo = cast(UserRepository, self.get_repository(Collection.USERS))
        admin_user_repo = self.get_repository(Collection.ADMIN_USERS)
        user = user_repo.get_user_by_email(email=new_user.email)
        if user is None:
            raise EntityNotFound(
                collection=Collection.USERS,
                attribute="email",
                value=new_user.email,
            )

        # Override to always use the provided user_id
        return admin_user_repo.create(
            CreateAdminUser(
                user_id=user.id,
                email=new_user.email,
                role=new_user.role,
            ),
            overridden_id=user.id,
        )
