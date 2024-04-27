"""
This is the main file of the API. It contains the FastAPI instance and the
routes of the API.

At the bottom of the file you will see the imported middleware functions
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ajb.vendor.sentry import initialize_sentry
from ajb.config.settings import SETTINGS
from api.admin.app import admin_router
from api.portal_api.app import portal_api_router
from api.open.app import open_router

from .middleware import (
    add_app_middleware,
    ValidationErrorLoggingMiddleware,
)


app = FastAPI(
    title="Angies Job Board API",
    description="The API for Angies Job Board",
    version=SETTINGS.APP_VERSION,
)

initialize_sentry()

app.include_router(admin_router)
app.include_router(portal_api_router)
app.include_router(open_router)


origins = [
    "*",
    "http://localhost:3000",
    "http://localhost:3001",
    "https://matcher.ajbdevelopment.com",
    "https://*.ajbdevelopment.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
add_app_middleware(app)
app.add_middleware(ValidationErrorLoggingMiddleware)
