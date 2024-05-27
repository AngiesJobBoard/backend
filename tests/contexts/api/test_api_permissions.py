from fastapi.testclient import TestClient
from ajb.fixtures.users import UserFixture

from tests.contexts.api.conftest import (
    portal_api_patches,
    admin_api_patches,
    AUTH_HEADER,
)


def test_portal_request_success(request_scope, api: TestClient):
    user = UserFixture(request_scope).create_user()
    request_scope.user_id = user.id
    with portal_api_patches(request_scope, "api.app.contexts.users.scope"):
        resp = api.get("/me/", headers=AUTH_HEADER)

    assert resp.status_code == 200


def test_admin_request_success(request_scope, api: TestClient):
    admin_user = UserFixture(request_scope).create_admin_user()
    request_scope.user_id = admin_user.id
    with admin_api_patches(request_scope, "api.admin.contexts.admin_users.scope"):
        resp = api.get("/admin/admin-users/me/", headers=AUTH_HEADER)

    assert resp.status_code == 200


def test_admin_request_user_not_exist(request_scope, api: TestClient):
    user = UserFixture(request_scope).create_user()
    request_scope.user_id = user.id
    with admin_api_patches(request_scope, "api.admin.contexts.admin_users.scope"):
        resp = api.get("/admin/admin-users/me/", headers=AUTH_HEADER)

    assert resp.status_code == 403
