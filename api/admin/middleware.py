from fastapi import Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from ajb.base import RequestScope
from ajb.contexts.admin.users.repository import AdminUserRepository, AdminUser
from ajb.exceptions import EntityNotFound
from api.middleware import decode_user_token
from api.exceptions import Forbidden
from api.vendors import db, kafka_producer


def get_admin_user(scope: RequestScope, user_id: str) -> AdminUser:
    try:
        return AdminUserRepository(scope).get_admin_user_by_auth_id(user_id)
    except EntityNotFound:
        raise Forbidden


async def verify_admin_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False)),
) -> None:
    user = decode_user_token(credentials.credentials)
    if user is None:
        raise Forbidden

    scope = RequestScope(
        user_id=user.id,
        db=db,
        kafka=kafka_producer,
    )
    admin_user = get_admin_user(scope, user.id)
    if admin_user is None:
        raise Forbidden
    request.state.request_scope = scope
    request.state.admin_user = admin_user


def admin_user(request: Request) -> AdminUser:
    return request.state.admin_user
