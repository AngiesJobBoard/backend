import pytest

from ajb.base.events import BaseKafkaMessage, KafkaTopic
from ajb.config.settings import SETTINGS
from ajb.contexts.users.models import CreateUser
from ajb.contexts.users.repository import UserRepository
from ajb.vendor.sendgrid.repository import SendgridRepository
from ajb.vendor.sendgrid.mock import MockSendgrid
from services.resolvers.users import UserEventResolver


@pytest.mark.asyncio
async def test_user_is_created(request_scope):
    user_repo = UserRepository(request_scope)

    # Create test user
    user_repo.create(
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

    mock_sendgrid = MockSendgrid()
    mock_sendgrid_repository = SendgridRepository(mock_sendgrid)  # type: ignore

    # Create user event resolver
    resolver = UserEventResolver(
        BaseKafkaMessage(
            data={"user_id": "test"},
            requesting_user_id="test",
            topic=KafkaTopic(SETTINGS.KAFKA_APPLICATIONS_TOPIC),
            event_type="test",
            source_service="my_service_name",
        ),
        request_scope,
        sendgrid=mock_sendgrid_repository,
    )

    # Testing
    await resolver.user_is_created()
    assert len(mock_sendgrid.sent_emails) == 1
    assert mock_sendgrid.sent_emails[0]["subject"].subject == "Welcome!"
