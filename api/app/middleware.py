from cachetools import TTLCache
from fastapi import Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from ajb.base import RequestScope
from ajb.contexts.companies.recruiters.repository import RecruiterRepository
from ajb.exceptions import EntityNotFound

from api.middleware import decode_user_token
from api.exceptions import Forbidden
from api.vendors import db, kafka_producer


RECRUITER_CACHE = TTLCache(maxsize=1000, ttl=60 * 5)  # 5 minutes cache ttl

class NoCompanyIdInPath(Exception):
    pass


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


def get_company_recruiter(request_scope: RequestScope, company_id: str, user_id: str):
    # First, check the cache
    cache_key = f"{company_id}-{user_id}"
    recruiter = RECRUITER_CACHE.get(cache_key)
    if recruiter:
        return recruiter
    
    # If not in cache, fetch from the database
    recruiter = RecruiterRepository(request_scope).get_recruiter_by_company_and_user(
        company_id, user_id
    )
    RECRUITER_CACHE[cache_key] = recruiter
    return recruiter



async def verify_user_and_company(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False)),
):
    user = decode_user_token(credentials.credentials)
    if user is None:
        raise Forbidden

    request_scope = RequestScope(
        user_id=user.id,
        db=db,
        kafka=kafka_producer,
    )
    request.state.request_scope = request_scope

    if request.url.path == "/companies/":
        # Do not need to verify for this specific endpoint
        return
    company_id = request.path_params.get("company_id")
    if not company_id:
        # Company ID must be in all paths in the company app
        raise NoCompanyIdInPath

    try:
        request.state.recruiter = get_company_recruiter(
            request_scope, company_id, user.id
        )
    except EntityNotFound:
        raise Forbidden
