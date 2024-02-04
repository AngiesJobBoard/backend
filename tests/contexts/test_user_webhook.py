from ajb.contexts.webhooks.users.usecase import (
    WebhookUserUseCase,
    ClerkUser,
    ClerkUserWebhookEvent,
    ClerkUserWebhookType,
)
from ajb.contexts.users.repository import UserRepository
from ajb.vendor.clerk.models import ClerkUserEmailAddresses, ClertkUserPhoneNumbers


def test_create_user_webhook(request_scope):
    webhook_repo = WebhookUserUseCase(request_scope)
    user_repo = UserRepository(request_scope)

    webhook_event = ClerkUserWebhookEvent(
        data=ClerkUser(
            id="test",
            object="user",
            created_at=123,
            primary_email_address_id="1",
            email_addresses=[
                ClerkUserEmailAddresses(
                    id="1",
                    object="email_address",
                    email_address="nice@email.com",
                )
            ],
            phone_numbers=[
                ClertkUserPhoneNumbers(
                    id="1",
                    object="phone_number",
                    phone_number="123",
                )
            ],
            first_name="test",
            last_name="test",
            gender="test",
            birthday="123",
        ).model_dump(),
        object="user",
        type=ClerkUserWebhookType.user_created,
    )

    webhook_response = webhook_repo.handle_webhook_event(webhook_event)
    assert webhook_response

    all_users, user_count = user_repo.query()
    assert len(all_users) == 1
    assert user_count == 1

    assert user_repo.get("test")
