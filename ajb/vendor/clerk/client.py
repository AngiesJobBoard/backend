from fastapi import HTTPException
from requests import request, Response

from ajb.config.settings import SETTINGS
from ajb.exceptions import EntityNotFound

from .models import ClerkCreateUser


class ClerkClient:
    def __init__(self):
        self.api_key = SETTINGS.CLERK_SECRET_KEY
        self.base_url = "https://api.clerk.dev"

    def _headers(self):
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _make_request(
        self,
        method: str,
        endpoint: str,
        payload: dict | None = None,
        files: dict | None = None,
    ) -> Response:
        url = self.base_url + endpoint
        request_payload = {"method": method, "url": url, "headers": self._headers()}
        if payload:
            request_payload["json"] = payload
        if files:
            request_payload["files"] = files
        response = request(**request_payload, timeout=10)
        if response.status_code == 404:
            raise EntityNotFound(endpoint)
        if response.status_code != 200:
            raise HTTPException(
                status_code=500, detail=f"Error: {response.status_code} {response.text}"
            )
        return response

    def get_user(self, user_id: str):
        endpoint = f"/v1/users/{user_id}"
        return self._make_request("GET", endpoint)

    def get_user_by_email(self, email: str):
        endpoint = f"/v1/users?email_address={email}"
        return self._make_request("GET", endpoint)

    def get_all_users(self):
        endpoint = "/v1/users"
        return self._make_request("GET", endpoint)

    def create_user(self, user_data: ClerkCreateUser):
        endpoint = "/v1/users"
        return self._make_request("POST", endpoint, payload=user_data.model_dump())

    def delete_user(self, user_id: str):
        endpoint = f"/v1/users/{user_id}"
        return self._make_request("DELETE", endpoint)

    def create_signin_token(self, user_id: str, expires_in_seconds: int = 3600):
        endpoint = "/v1/sign_in_tokens"
        return self._make_request(
            "POST",
            endpoint,
            payload={"user_id": user_id, "expires_in_seconds": expires_in_seconds},
        )

    def revoke_signin_token(self, sign_in_token_id: str):
        endpoint = f"/v1/sign_in_tokens/{sign_in_token_id}/revoke"
        return self._make_request("POST", endpoint)
