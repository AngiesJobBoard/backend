from fastapi.testclient import TestClient

from ajb.contexts.users.repository import UserRepository
from ajb.fixtures.users import UserFixture
from tests.contexts.api.conftest import portal_api_patches, AUTH_HEADER


ROUTER_PATH = "api.app.contexts.users.scope"


def test_get_me(request_scope, api: TestClient):
    user = UserFixture(request_scope).create_user()
    request_scope.user_id = user.id
    with portal_api_patches(request_scope, ROUTER_PATH):
        resp = api.get("/me/", headers=AUTH_HEADER)

    assert resp.status_code == 200
    assert resp.json()["id"] == user.id


def test_update_current_user(request_scope, api: TestClient):
    user = UserFixture(request_scope).create_user()
    request_scope.user_id = user.id
    with portal_api_patches(request_scope, ROUTER_PATH):
        resp = api.patch("/me/", headers=AUTH_HEADER, json={"first_name": "New Name"})

    assert resp.status_code == 200
    assert resp.json()["first_name"] == "New Name"

    user_from_db = UserRepository(request_scope).get(user.id)
    assert user_from_db.first_name == "New Name"
