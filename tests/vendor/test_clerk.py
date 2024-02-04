import secrets
from pydantic import BaseModel
from requests import Response

from ajb.vendor.clerk.repository import ClerkAPIRepository
from ajb.vendor.clerk.models import ClerkCreateUser
from ajb.vendor.clerk.mock import MockClerkClient


class ExampleModel(BaseModel):
    test: str


TEST_EMAIL = "nice@email.com"


class TestClerkAPI:
    repository = ClerkAPIRepository(MockClerkClient())

    def test_format_response_to_model(self):
        response = Response()
        response.json = lambda: {"data": {"test": "data"}}  # type: ignore
        assert self.repository._format_response_to_model(response, ExampleModel)

    def test_get_user(self):
        assert self.repository.get_user("test")

    def test_get_all_users(self):
        assert self.repository.get_all_users()

    def test_create_user(self):
        assert self.repository.create_user(
            ClerkCreateUser(
                first_name="test",
                last_name="test",
                password=secrets.token_hex(16),
                skip_password_checks=True,
                skip_password_requirement=True,
                email_address=[TEST_EMAIL],
            )
        )

    def test_delete_user(self):
        created_user = self.repository.create_user(
            ClerkCreateUser(
                first_name="test",
                last_name="test",
                password=secrets.token_hex(16),
                skip_password_checks=True,
                skip_password_requirement=True,
                email_address=[TEST_EMAIL],
            )
        )
        self.repository.delete_user(created_user.id)

    def create_signin_token(self):
        created_user = self.repository.create_user(
            ClerkCreateUser(
                first_name="test",
                last_name="test",
                password=secrets.token_hex(16),
                skip_password_checks=True,
                skip_password_requirement=True,
                email_address=[TEST_EMAIL],
            )
        )
        self.repository.create_signin_token(created_user.id)

    def revoke_signing_token(self):
        created_user = self.repository.create_user(
            ClerkCreateUser(
                first_name="test",
                last_name="test",
                password=secrets.token_hex(16),
                skip_password_checks=True,
                skip_password_requirement=True,
                email_address=[TEST_EMAIL],
            )
        )
        signin_token = self.repository.create_signin_token(created_user.id)
        self.repository.revoke_signing_token(signin_token.id)
