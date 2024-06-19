import asyncio
from unittest.mock import MagicMock
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from ajb.base.events import BaseKafkaMessage
from ajb.config.settings import SETTINGS
from ajb.contexts.users.models import CreateUser
from ajb.contexts.users.repository import UserRepository
from ajb.vendor.sendgrid.repository import SendgridRepository
from services.resolvers.users import UserEventResolver


def test_user_is_created(request_scope):
    user_repo = UserRepository(request_scope)

    # Create test user
    user = user_repo.create(
        CreateUser(
            first_name="test",
            last_name="test",
            email="test@email.com",
            image_url="test",
            phone_number="test",
            auth_id="test_id",
        ),
        overridden_id="test",
    )

    # Create mock sendgrid client
    mock_sendgrid = MagicMock(spec=SendGridAPIClient)
    mock_sendgrid.send = MagicMock()
    mock_sendgrid_repository = SendgridRepository(mock_sendgrid)

    # Create user event resolver
    resolver = UserEventResolver(
        BaseKafkaMessage(
            data={"user_id": "test"},
            requesting_user_id="test",
            topic=SETTINGS.KAFKA_APPLICATIONS_TOPIC,
            event_type="test",
            source_service="my_service_name",
        ),
        request_scope,
        sendgrid=mock_sendgrid_repository,
    )

    # Testing
    asyncio.run(resolver.user_is_created())

    mail_call = mock_sendgrid.send.call_args[0][0]
    assert isinstance(mail_call, Mail)

    # Verify the email in personalizations
    assert (
        mail_call.personalizations[0].tos[0]["email"] == user.email
    )  # Assert user email is correct
    assert mail_call.subject.subject == "Welcome!"  # Assert welcome message
