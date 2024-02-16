from unittest.mock import patch
import secrets
import pytest

from ajb.exceptions import EntityNotFound
from ajb.contexts.users.models import CreateUser
from ajb.contexts.users.repository import UserRepository
from ajb.contexts.users.usecase import UserUseCase
from ajb.contexts.webhooks.users.usecase import WebhookUserUseCase
from ajb.vendor.clerk.models import (
    SimpleClerkCreateUser,
    ClerkUserWebhookEvent,
    ClerkUserWebhookType,
    ClerkUser,
)
from ajb.vendor.clerk.mock import mock_clerk_user
from ajb.exceptions import AdminCreateUserException


@pytest.fixture(scope="function")
def user_repo(request_scope):
    return UserRepository(request_scope)


def test_user_repo(user_repo: UserRepository):
    # Create
    user = user_repo.create(
        CreateUser(
            first_name="test",
            last_name="test",
            email="test@email.com",
            image_url="test",
            phone_number="test",
            auth_id="test_id",
        ),
        overridden_id="test_id",
    )

    # Read
    read_user = user_repo.get("test_id")
    assert read_user.first_name == "test"
    assert read_user.last_name == "test"
    assert read_user.email == user.email

    # Update
    updated_user = user_repo.update_fields(read_user.id, first_name="Bob")
    assert updated_user.first_name == "Bob"

    read_user = user_repo.get("test_id")
    assert read_user.first_name == "Bob"

    # Query
    queried_user = user_repo.get_user_by_email(user.email)
    assert queried_user.first_name == "Bob"

    birth_year_query, count = user_repo.query(phone_number="test")
    assert count == 1
    assert birth_year_query[0].first_name == "Bob"

    # Delete
    user_repo.delete("test_id")
    with pytest.raises(EntityNotFound):
        user_repo.get("test_id")


def test_admin_create_user(request_scope):
    # Create user with use case
    created_user = UserUseCase(request_scope).admin_create_user(
        SimpleClerkCreateUser(
            first_name="test",
            last_name="test",
            email_address="test@email.com",
            password=secrets.token_hex(16),
        )
    )
    # Handle same user sent to webhook by Clerk
    mock_clerk_user.private_metadata = {"created_by_admin": True}
    clerk_user = ClerkUser(**mock_clerk_user.model_dump())
    response = WebhookUserUseCase(request_scope).create_user(
        ClerkUserWebhookEvent(
            data=clerk_user.model_dump(),
            object="user",
            type=ClerkUserWebhookType.user_created,
        ),
    )
    assert response is True

    user_repo = UserRepository(request_scope)
    assert user_repo.get(created_user.id)


def test_admin_create_user_force(request_scope):
    usecase = UserUseCase(request_scope)

    with patch(
        "ajb.vendor.clerk.repository.ClerkAPIRepository.get_user_by_email"
    ) as mock_get_user:
        mock_get_user.return_value = ClerkUser(**mock_clerk_user.model_dump())

        # Get admin create error if user exists in clerk already and not forcing
        with pytest.raises(AdminCreateUserException):
            usecase.admin_create_user(
                SimpleClerkCreateUser(
                    first_name="test",
                    last_name="test",
                    email_address="test@email.com",
                    password=secrets.token_hex(16),
                )
            )

        # Creation continues if forcing is enabled
        usecase.admin_create_user(
            SimpleClerkCreateUser(
                first_name="test",
                last_name="test",
                email_address="test@email.com",
                password=secrets.token_hex(16),
            ),
            force_if_exists=True,
        )


def test_bad_type_output(request_scope):
    usecase = UserUseCase(request_scope)
    with patch(
        "ajb.contexts.webhooks.users.usecase.WebhookUserUseCase.create_user"
    ) as mock_create:
        mock_create.return_value = True
        with pytest.raises(AdminCreateUserException):
            usecase.admin_create_user(
                SimpleClerkCreateUser(
                    first_name="test",
                    last_name="test",
                    email_address="test@email.com",
                    password=secrets.token_hex(16),
                ),
                force_if_exists=True,
            )
