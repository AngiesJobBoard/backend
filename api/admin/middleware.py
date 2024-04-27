from cachetools import TTLCache, cached
from fastapi import Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from ajb.base import RequestScope
from ajb.contexts.admin.users.repository import AdminUserRepository, AdminUser
from api.middleware import decode_user_token
from api.exceptions import Forbidden
from api.vendors import db, kafka_producer


@cached(cache=TTLCache(maxsize=1024, ttl=300))
def get_admin_user(scope: RequestScope, user_id: str) -> AdminUser:
    admin_user = AdminUserRepository(scope).get_admin_user_by_auth_id(user_id)
    if admin_user is None:
        raise Forbidden
    return admin_user


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
    request.state.request_scope = scope
    request.state.admin_user = admin_user


def admin_user(request: Request) -> AdminUser:
    return request.state.admin_user
