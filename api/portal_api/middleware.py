from cachetools import TTLCache, cached
from fastapi import Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from ajb.base import RequestScope
from ajb.contexts.companies.recruiters.repository import RecruiterRepository
from ajb.exceptions import EntityNotFound

from api.middleware import decode_user_token, scope
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


@cached(TTLCache(maxsize=1000, ttl=60))
async def user_has_access_to_company(
    request: Request,
    company_id: str,
) -> None:
    try:
        RecruiterRepository(scope(request)).get_recruiter_by_company_and_user(
            company_id, scope(request).user_id
        )
    except EntityNotFound:
        raise Forbidden

    # AJBTODO update actions based permissions based on role
