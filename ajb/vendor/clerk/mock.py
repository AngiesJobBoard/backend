from requests import Response

from .models import ClerkUser
from .client import ClerkClient


mock_clerk_user = ClerkUser(
    id="abc123",
    object="nice",
    created_at=123,
    primary_email_address_id="abc123",
    email_addresses=[],
    phone_numbers=[],
    first_name="John",
    last_name="Doe",
    gender="male",
    birthday="1990-01-01",
    private_metadata={},
)


class MockClerkClient(ClerkClient):
    # pylint: disable=super-init-not-called
    def __init__(self, *args, **kwargs): ...

    def _make_request(self, *args, **kwargs):
        resp = Response()
        resp.status_code = 200
        resp.json = lambda: kwargs["json"]  # type: ignore
        return resp

    def get_user(self, *args, **kwargs):
        return self._make_request(json=mock_clerk_user.model_dump())

    def get_user_by_email(self, *args, **kwargs):
        return self._make_request(json=mock_clerk_user.model_dump())

    def get_all_users(self):
        return self._make_request(json=[mock_clerk_user.model_dump()])

    def create_user(self, *args, **kwargs):
        return self._make_request(json=mock_clerk_user.model_dump())

    def delete_user(self, *args, **kwargs):
        return self._make_request(json={"deleted": True})

    def create_signin_token(self, *args, **kwargs):
        return self._make_request(json={"token": "abc"})

    def revoke_signin_token(self, *args, **kwargs):
        return self._make_request(json={"revoked": True})
