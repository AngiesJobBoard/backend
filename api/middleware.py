import os
import time
import logging
from typing import Callable

import jwt
from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware

from ajb.config.settings import SETTINGS
from ajb.base import RequestScope
from ajb.contexts.users.sessions.models import SessionData

from api.exceptions import InvalidToken


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def decode_user_token(token: str) -> SessionData:
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


def log_request_info(
    request: Request, user: SessionData | None, status_code: int, process_time: float
) -> None:
    """
    Generate a log message with information about the incoming request.
    """

    # Extract relevant information from the request object
    client_host = request.client
    method = request.method
    url = request.url.path
    query_params = dict(request.query_params)
    path_params = dict(request.path_params)

    # Create the log message
    log_message = {
        "status_code": status_code,
        "process_time": process_time,
        "user_id": user.id if user else "anonymous",
        "client_host": client_host.host if client_host else "unknown",
        "method": method,
        "url": url,
        "query_params": query_params,
        "path_params": path_params,
    }
    logger.info("ajbLOG: %s", log_message)


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


class ValidationErrorLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        if response.status_code == 422:
            body = b""
            async for chunk in response.body_iterator:  # type: ignore
                body += chunk
            raise RuntimeError(f"Validation error: {body.decode()}")
        return response


def scope(request: Request) -> RequestScope:
    return request.state.request_scope
