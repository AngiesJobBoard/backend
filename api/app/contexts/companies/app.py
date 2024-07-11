from fastapi import APIRouter, Depends

from api.app.contexts.companies import (
    ai_generator,
    application_recruiter_updates,
    applications,
    companies,
    create_applications,
    egress_webhooks,
    ingress_webhooks,
    invitations,
    job_email_ingress,
    jobs,
    notifications,
    recruiters,
    raw_api_ingress,
    subscriptions,
)
from api.app.middleware import (
    verify_user_and_company,
    verify_company_subscription_exists,
)

company_api_router = APIRouter(dependencies=[Depends(verify_user_and_company)])

company_api_router.include_router(
    ai_generator.router, dependencies=[Depends(verify_company_subscription_exists)]
)
company_api_router.include_router(application_recruiter_updates.router)
company_api_router.include_router(applications.router)
company_api_router.include_router(subscriptions.router)
company_api_router.include_router(companies.router)
company_api_router.include_router(
    egress_webhooks.router, dependencies=[Depends(verify_company_subscription_exists)]
)
company_api_router.include_router(
    ingress_webhooks.router, dependencies=[Depends(verify_company_subscription_exists)]
)
company_api_router.include_router(invitations.router)
company_api_router.include_router(
    create_applications.router,
    dependencies=[Depends(verify_company_subscription_exists)],
)
company_api_router.include_router(job_email_ingress.router)
company_api_router.include_router(jobs.router)
company_api_router.include_router(notifications.router)
company_api_router.include_router(recruiters.router)
company_api_router.include_router(
    raw_api_ingress.router, dependencies=[Depends(verify_company_subscription_exists)]
)
