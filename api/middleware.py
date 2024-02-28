import os
import time
import logging
from typing import Callable
from cachetools import TTLCache

import jwt
from fastapi import FastAPI, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from ajb.config.settings import SETTINGS
from ajb.base import RequestScope
from ajb.contexts.users.sessions.models import SessionData
from ajb.contexts.companies.recruiters.repository import (
    RecruiterRepository,
    CompanyAndRole,
)

from .exceptions import Forbidden, InvalidToken
from .vendors import db, kafka_producer


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


USER_COMPANY_CACHE = TTLCache(
    maxsize=100, ttl=3600
)  # TO BECOME a redis cache as necessary


PUBLIC_ROUTES = [
    "/docs",
    "/openapi.json",
    "/webhooks/clerk/users",
    "/webhooks/clerk/companies",
    "/webhooks/clerk/recruiters",
    "/webhooks/clerk/recruiter-invitations",
    "/health/check",
    "/health/version",
    "/search/jobs/",
]

LOGGING_EXCLUDED_ROUTES = [
    "/health/check",
    "/health/version",
    "/docs",
    "/openapi.json",
    "/search/jobs",
    "/search/jobs/autocomplete",
    "/search/jobs/categories",
    "/search/jobs/{job_id}",
]


def get_user(token: str):
    """
    This function decodes the JWT token and returns the user data
    """
    try:
        decoded_token = jwt.decode(
            token,
            SETTINGS.CLERK_JWT_PEM_KEY,
            algorithms=["RS256"],
            leeway=SETTINGS.CLERK_TOKEN_LEEWAY,
        )
        return SessionData(**decoded_token)
    except jwt.DecodeError:
        raise InvalidToken
    except jwt.ExpiredSignatureError:
        raise InvalidToken(detail="Token expired")


def get_company_id_from_request(request: Request):
    """Get the company_id from the request"""
    if "companies" in request.url.path and "company_id" in request.path_params:
        return request.path_params["company_id"]
    return None


def log_request_info(
    request: Request, user: SessionData | None, status_code: int, process_time: float
) -> None:
    """
    Generate a log message with information about the incoming request.
    """
    if request.url.path in LOGGING_EXCLUDED_ROUTES:
        return

    # Extract relevant information from the request object
    client_host = request.client
    method = request.method
    url = request.url.path
    query_params = dict(request.query_params)
    path_params = dict(request.path_params)
    company_id = get_company_id_from_request(request)

    # Create the log message
    log_message = {
        "status_code": status_code,
        "process_time": process_time,
        "company_id": company_id,
        "user_id": user.id if user else "anonymous",
        "client_host": client_host.host if client_host else "unknown",
        "method": method,
        "url": url,
        "query_params": query_params,
        "path_params": path_params,
    }
    logger.info("ajbLOG: %s", log_message)


async def get_companies_from_user(request_scope: RequestScope) -> list[CompanyAndRole]:
    if request_scope.user_id in USER_COMPANY_CACHE:
        return USER_COMPANY_CACHE[request_scope.user_id]
    results = RecruiterRepository(request_scope).get_companies_by_user_id(
        request_scope.user_id
    )
    USER_COMPANY_CACHE[request_scope.user_id] = results
    return results


async def verify_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False)),
):
    """
    This function verifies the user on every request to the API
    or sets them as anonymous
    """

    request.state.user = None
    request.state.companies = []
    if credentials and credentials.credentials:
        # User trying to authenticate
        request.state.user = get_user(credentials.credentials)

    if request.url.path not in PUBLIC_ROUTES and not request.state.user:
        raise Forbidden

    if request.state.user:
        request.state.request_scope = RequestScope(
            user_id=request.state.user.id,
            db=db,
            kafka_producer=kafka_producer,
            company_id=None,
        )
        request.state.companies = await get_companies_from_user(
            request.state.request_scope
        )
        request.state.request_scope.company_id = get_company_id_from_request(
            request
        ) or (
            request.state.companies[0].company_id if request.state.companies else None
        )
    else:
        ip_address = request.client.host if request.client else "unknown_ip"
        request.state.request_scope = RequestScope.create_anonymous_user_scope(
            ip_address=ip_address,
            db=db,
            kafka_producer=kafka_producer,
        )


async def get_connection_from_token(bearer_token: str, company_id: str | None):
    """Used with websockets to get the connection from the token"""
    user = get_user(bearer_token)
    return RequestScope(
        user_id=user.id, db=db, kafka_producer=kafka_producer, company_id=company_id
    )


def add_app_middleware(app: FastAPI):
    @app.middleware("http")
    async def add_process_time_header(request: Request, call_next: Callable):
        start_time = time.time()

        if os.getenv("APP_IS_SLOW") == "true":
            time.sleep(1)

        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        try:
            user = request.state.user
        except AttributeError:
            user = None

        log_request_info(request, user, response.status_code, round(process_time, 4))
        return response
