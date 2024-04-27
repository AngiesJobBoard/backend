from fastapi import Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from ajb.base import RequestScope

from api.middleware import decode_user_token
from api.exceptions import Forbidden
from api.vendors import db, kafka_producer


async def verify_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False)),
) -> None:
    user = decode_user_token(credentials.credentials)
    if user is None:
        raise Forbidden
    request.state.request_scope = RequestScope(
        user_id=user.id,
        db=db,
        kafka=kafka_producer,
    )
