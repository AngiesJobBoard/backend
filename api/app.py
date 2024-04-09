"""
This is the main file of the API. It contains the FastAPI instance and the
routes of the API.

At the bottom of the file you will see the imported middleware functions
"""

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from ajb.vendor.sentry import initialize_sentry
from ajb.config.settings import SETTINGS

from api.contexts.admin.search import router as admin_search_router
from api.contexts.admin.admin_users import router as admin_users_router
from api.contexts.admin.admin_jobs import router as admin_jobs_router
from api.contexts.admin.general_admin import router as general_admin_router

from api.contexts.users.users import router as users_router

from api.contexts.companies.companies import router as companies_router
from api.contexts.companies.invitations import router as company_invitations_router
from api.contexts.companies.recruiters import router as recruiters_router
from api.contexts.companies.jobs import router as jobs_router
from api.contexts.companies.job_applications import router as job_applications_router
from api.contexts.companies.applications import router as company_applications_router
from api.contexts.companies.application_recruiter_updates import (
    router as application_updates_router,
)
from api.contexts.companies.notifications import router as company_notifications_router
from api.contexts.companies.ai_generator import (
    router as ai_generator_router,
)
from api.contexts.companies.egress_webhooks import router as egress_webhooks_router
from api.contexts.companies.job_email_ingress import router as job_email_ingress_router
from api.contexts.companies.billing import router as company_billing_router

from api.contexts.webhooks.clerk import router as clerk_webhooks_router
from api.contexts.webhooks.companies import router as companies_webhooks_router
from api.contexts.static.static_data import router as static_data_router
from api.contexts.static.enumerations import router as static_enumerations_router
from api.contexts.admin.users import router as admin_create_users_router
from api.contexts.health.health import router as health_router

from .middleware import (
    add_app_middleware,
    verify_user,
    ValidationErrorLoggingMiddleware,
)


app = FastAPI(
    title="Angies Job Board API",
    description="The public facing API for Angies Job Board",
    version=SETTINGS.APP_VERSION,
    dependencies=[Depends(verify_user)],
)

initialize_sentry()

app.include_router(users_router)

app.include_router(companies_router)
app.include_router(company_invitations_router)
app.include_router(recruiters_router)
app.include_router(jobs_router)
app.include_router(job_applications_router)
app.include_router(company_applications_router)
app.include_router(application_updates_router)
app.include_router(company_notifications_router)
app.include_router(ai_generator_router)
app.include_router(egress_webhooks_router)
app.include_router(job_email_ingress_router)
app.include_router(company_billing_router)

app.include_router(clerk_webhooks_router)
app.include_router(companies_webhooks_router)

app.include_router(static_data_router)
app.include_router(static_enumerations_router)

app.include_router(admin_search_router)
app.include_router(admin_users_router)
app.include_router(admin_create_users_router)
app.include_router(admin_jobs_router)
app.include_router(general_admin_router)

app.include_router(health_router)


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
