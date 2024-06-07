from fastapi import APIRouter, Depends

from api.app.contexts.companies import (
    ai_generator,
    application_recruiter_updates,
    applications,
    billing,
    companies,
    create_applications,
    egress_webhooks,
    ingress_webhooks,
    invitations,
    job_email_ingress,
    job_interview_rubrics,
    job_interview_questions,
    jobs,
    notifications,
    raw_api_ingress,
    recruiters,
)
from api.app.middleware import user_has_access_to_company, verify_user

company_api_router = APIRouter(
    tags=["Company"],
    dependencies=[Depends(verify_user)],
)

company_api_router.include_router(ai_generator.router)
company_api_router.include_router(application_recruiter_updates.router)
company_api_router.include_router(applications.router)
company_api_router.include_router(billing.router)
company_api_router.include_router(companies.router)
company_api_router.include_router(egress_webhooks.router)
company_api_router.include_router(ingress_webhooks.router)
company_api_router.include_router(invitations.router)
company_api_router.include_router(create_applications.router)
company_api_router.include_router(job_email_ingress.router)
company_api_router.include_router(jobs.router)
company_api_router.include_router(notifications.router)
company_api_router.include_router(recruiters.router)
company_api_router.include_router(raw_api_ingress.router)
company_api_router.include_router(job_interview_rubrics.router)
company_api_router.include_router(job_interview_questions.router)
