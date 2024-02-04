import typing as t

from ajb.base import BaseUseCase, Collection
from ajb.contexts.users.repository import CreateUser, User
from ajb.exceptions import EntityNotFound

from ajb.vendor.clerk.models import (
    ClerkUser,
    ClerkUserWebhookEvent,
    ClerkUserWebhookType,
)


class WebhookUserUseCase(BaseUseCase):
    def handle_webhook_event(self, event: ClerkUserWebhookEvent) -> t.Any:
        event_dict = {
            ClerkUserWebhookType.user_created: self.create_user,
        }
        return event_dict[event.type](event)

    def create_user(
        self,
        event: ClerkUserWebhookEvent,
        return_user: bool = False,
        internal_creation: bool = False,
    ) -> bool | User:
        user_repo = self.get_repository(Collection.USERS)
        create_event = ClerkUser(**event.data)

        # Check for created by admin flag and skip
        if (
            create_event.private_metadata.get("created_by_admin")
            and not internal_creation
        ):
            return True

        created_user: User = user_repo.create(
            CreateUser(
                first_name=create_event.first_name,
                last_name=create_event.last_name,
                email=create_event.email,
                image_url=create_event.image_url,
                phone_number=create_event.phone_number,
                auth_id=create_event.id,
                candidate_score=0,
            ),
            overridden_id=create_event.id,
        )
        return created_user if return_user else True
