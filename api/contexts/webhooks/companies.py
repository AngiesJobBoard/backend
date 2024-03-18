from fastapi import APIRouter, status, Request

from ajb.base import RequestScope
from ajb.contexts.webhooks.jobs.models import JobsWebhook
from ajb.contexts.webhooks.jobs.usecase import WebhookJobsUseCase
from api.vendors import db

from api.middleware import WebhookValidator


WEBHOOK_REQUEST_SCOPE = RequestScope(
    user_id="companies_webhook", db=db, company_id=None
)


router = APIRouter(
    tags=["Webhooks"],
    prefix="/webhooks/companies",
)

@router.post("/api-ingress/jobs", status_code=status.HTTP_204_NO_CONTENT)
async def jobs_api_webhook_handler(request: Request, payload: JobsWebhook):
    # TODO better handle this in middleware instead of individually
    company_id = WebhookValidator(request).validate_api_ingress_request()
    WebhookJobsUseCase(WEBHOOK_REQUEST_SCOPE).handle_webhook_event(company_id, payload)


@router.post("/api-ingress/applicants", status_code=status.HTTP_204_NO_CONTENT)
async def applicants_api_webhook_handler(request: Request):
    print(request.__dict__)


@router.post("/email-ingress/jobs", status_code=status.HTTP_204_NO_CONTENT)
async def jobs_email_webhook_handler(request: Request):
    print(request.__dict__)


@router.post("/email-ingress/applicants", status_code=status.HTTP_204_NO_CONTENT)
async def applicants_email_webhook_handler(request: Request):
    print(request.__dict__)
