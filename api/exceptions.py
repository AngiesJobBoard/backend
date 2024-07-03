from cachetools import TTLCache, LRUCache
from fastapi import Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from ajb.base import RequestScope
from ajb.contexts.companies.recruiters.repository import RecruiterRepository, Recruiter
from ajb.contexts.billing.subscriptions.repository import CompanySubscriptionRepository
from ajb.contexts.billing.subscriptions.models import SubscriptionStatus
from ajb.exceptions import EntityNotFound

from api.middleware import decode_user_token
from api.exceptions import Forbidden, NoSubscription
from api.vendors import db, kafka_producer


RECRUITER_CACHE: TTLCache[str, Recruiter] = TTLCache(
    maxsize=1000, ttl=60 * 5
)  # 5 minutes cache ttl
SUBSCRIPTION_CACHE: LRUCache[str, bool] = LRUCache(maxsize=1000)


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


def company_has_subsription(request_scope: RequestScope, company_id: str) -> bool:
    # First, check the cache
    if SUBSCRIPTION_CACHE.get(company_id):
        return True
    try:
        subscription = CompanySubscriptionRepository(
            request_scope, company_id
        ).get_sub_entity()
        assert subscription.subscription_status == SubscriptionStatus.ACTIVE
        SUBSCRIPTION_CACHE[company_id] = True
        return True
    except (
        EntityNotFound,
        AssertionError,
    ):
        return False


async def verify_company_subscription_exists(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False)),
):
    """
    Assuming the user validation has passed,
    just check that the company being accessed has a subscription yes or no
    """
    CHECK_EXCLUDED_PATHS = []
    if request.url.path in CHECK_EXCLUDED_PATHS:
        # Do not need to verify subscription for these endpoints
        return

    user = decode_user_token(credentials.credentials)
    request_scope = RequestScope(
        user_id=user.id,
        db=db,
        kafka=kafka_producer,
    )
    company_id = request.path_params.get("company_id")
    if not company_id:
        # Company ID must be in all paths in the company app
        raise NoCompanyIdInPath

    if not company_has_subsription(request_scope, company_id):
        raise NoSubscription
