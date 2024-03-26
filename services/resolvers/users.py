"""
This module contains the asyncronous event handlers for the user context.
These are triggered when a user event is published to the Kafka topic
and is then routed to the appropriate handler based on the event type.
"""

from ajb.base import RequestScope
from ajb.base.events import BaseKafkaMessage
from ajb.vendor.clerk.repository import ClerkAPIRepository
from ajb.contexts.users.repository import UserRepository
from ajb.vendor.sendgrid.templates.new_user import NewlyCreatedUser
from ajb.vendor.openai.repository import OpenAIRepository
from ajb.vendor.sendgrid.repository import SendgridRepository


class UserEventResolver:
    def __init__(
        self,
        message: BaseKafkaMessage,
        request_scope: RequestScope,
        openai: OpenAIRepository | None = None,
        sendgrid: SendgridRepository | None = None,
        clerk: ClerkAPIRepository | None = None,
    ):
        self.message = message
        self.request_scope = request_scope
        self.openai = openai or OpenAIRepository()
        self.sendgrid = sendgrid or SendgridRepository()
        self.clerk = clerk or ClerkAPIRepository()

    async def user_is_created(self) -> None:
        user = UserRepository(self.request_scope).get(self.message.data["user_id"])
        self.sendgrid.send_email_template(
            to_emails=user.email,
            subject="Welcome!",
            template_data=NewlyCreatedUser(userFirstName=user.first_name),
        )
