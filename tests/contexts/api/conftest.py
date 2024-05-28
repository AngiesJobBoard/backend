from contextlib import contextmanager
from unittest.mock import patch

from ajb.base import RequestScope
from ajb.contexts.users.sessions.models import SessionData
from ajb.contexts.admin.users.repository import AdminUserRepository


AUTH_HEADER = {"authorization": "Bearer abc"}


@contextmanager
def portal_api_patches(request_scope: RequestScope, path_to_router: str):
    with patch("api.app.middleware.decode_user_token") as mock_token:
        mock_token.return_value = SessionData(
            id=request_scope.user_id, actor={}, public_meta={}
        )
        with patch(path_to_router) as mock_scope:
            mock_scope.return_value = request_scope
            yield


@contextmanager
def admin_api_patches(request_scope: RequestScope, path_to_router: str):
    admin_user_repo = AdminUserRepository(request_scope)
    try:
        admin_user = admin_user_repo.get_admin_user_by_auth_id(request_scope.user_id)
    except Exception:
        admin_user = None
    with patch("api.admin.middleware.decode_user_token") as mock_token:
        mock_token.return_value = SessionData(
            id=request_scope.user_id, actor={}, public_meta={}
        )
        with patch("api.admin.middleware.get_admin_user") as mock_admin_repo:
            mock_admin_repo.return_value = admin_user
            with patch(path_to_router) as mock_scope:
                mock_scope.return_value = request_scope
                yield
