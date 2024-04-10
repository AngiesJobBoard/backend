import typing
from requests import Response
from pydantic import BaseModel

from .client import ClerkClient
from .client_factory import ClerkClientFactory
from .models import (
    ClerkCreateUser,
    SignInToken,
    ClerkUser,
)


class ClerkAPIRepository:
    def __init__(self, client: ClerkClient | None = None):
        self.client = client or ClerkClientFactory.get_client()

    def _format_response_to_model(
        self, response: Response, model: typing.Type[BaseModel] | None
    ):
        """
        Some clerk models return a 'data' key and others don't. This method
        formats the response to a pydantic model for both cases
        """
        response_json = response.json()
        if "data" in response_json:
            response_json = response_json["data"]
        if not model:
            return response_json
        if isinstance(response_json, list):
            return [model(**item) for item in response_json]
        return model(**response_json)

    def get_user(self, user_id: str):
        user = self.client.get_user(user_id)
        return self._format_response_to_model(user, ClerkUser)

    def get_user_by_email(self, email: str):
        poential_user = self.client.get_user_by_email(email)
        converted_users = self._format_response_to_model(poential_user, ClerkUser)
        if isinstance(converted_users, list) and len(converted_users) > 0:
            return converted_users[0]
        return None

    def get_all_users(self):
        users = self.client.get_all_users()
        return self._format_response_to_model(users, ClerkUser)

    def create_user(self, user_data: ClerkCreateUser) -> ClerkUser:
        user = self.client.create_user(user_data)
        return self._format_response_to_model(user, ClerkUser)  # type: ignore

    def delete_user(self, user_id: str) -> bool:
        resp = self.client.delete_user(user_id)
        return resp.json()["deleted"]

    def create_signin_token(self, user_id: str) -> SignInToken:
        token = self.client.create_signin_token(user_id)
        return self._format_response_to_model(token, SignInToken)  # type: ignore

    def revoke_signing_token(self, token_id: str) -> bool:
        resp = self.client.revoke_signin_token(token_id)
        return resp.status_code == 200

    def verify_user_password(self, user_id: str, password_to_verify: str) -> bool:
        resp = self.client.verify_user_password(user_id, password_to_verify)
        return resp.status_code == 200

    def update_user_password(self, user_id: str, new_password: str) -> bool:
        resp = self.client.update_user_password(user_id, new_password)
        return resp.status_code == 200

    def set_and_verify_new_email_address(self, user_id: str, new_email: str) -> bool:
        resp = self.client.set_and_verify_new_email_address(user_id, new_email)
        return resp.status_code == 200
