from fastapi import APIRouter, Depends

from api.portal_api.contexts import (
    ai_generator,
    application_recruiter_updates,
    applications,
    billing,
    companies,
    egress_webhooks,
    enumerations,
    health,
    ingress_webhooks,
    invitations,
    job_applications,
    job_email_ingress,
    jobs,
    notifications,
    recruiters,
    static_data,
    users,
)
from api.portal_api.middleware import verify_user

portal_api_router = APIRouter(
    tags=["Portal"],
    dependencies=[Depends(verify_user)],
)

portal_api_router.include_router(ai_generator.router)
portal_api_router.include_router(application_recruiter_updates.router)
portal_api_router.include_router(applications.router)
portal_api_router.include_router(billing.router)
portal_api_router.include_router(companies.router)
portal_api_router.include_router(egress_webhooks.router)
portal_api_router.include_router(enumerations.router)
portal_api_router.include_router(health.router)
portal_api_router.include_router(ingress_webhooks.router)
portal_api_router.include_router(invitations.router)
portal_api_router.include_router(job_applications.router)
portal_api_router.include_router(job_email_ingress.router)
portal_api_router.include_router(jobs.router)
portal_api_router.include_router(notifications.router)
portal_api_router.include_router(recruiters.router)
portal_api_router.include_router(static_data.router)
portal_api_router.include_router(users.router)
