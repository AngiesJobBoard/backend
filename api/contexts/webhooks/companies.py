from fastapi import APIRouter, status, Request, Form

from ajb.base import RequestScope
from ajb.contexts.webhooks.jobs.models import JobsWebhook
from ajb.contexts.webhooks.jobs.usecase import WebhookJobsUseCase
from ajb.contexts.webhooks.applicants.models import ApplicantsWebhook
from ajb.contexts.webhooks.applicants.usecase import WebhookApplicantsUseCase
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
    company_id = WebhookValidator(request).validate_api_ingress_request()
    WebhookJobsUseCase(WEBHOOK_REQUEST_SCOPE).handle_webhook_event(company_id, payload)


@router.post("/api-ingress/applicants", status_code=status.HTTP_204_NO_CONTENT)
async def applicants_api_webhook_handler(request: Request, payload: ApplicantsWebhook):
    company_id = WebhookValidator(request).validate_api_ingress_request()
    WebhookApplicantsUseCase(WEBHOOK_REQUEST_SCOPE).handle_webhook_event(company_id, payload)


@router.post("/email-ingress/jobs", status_code=status.HTTP_204_NO_CONTENT)
async def jobs_email_webhook_handler(
    request: Request,
    envelope: str = Form(...),
    email: str = Form(...),
):
    ingress_record = WebhookValidator(request).validate_email_ingress_request(envelope)
    print(f"Processing email ingress for record {ingress_record}")


@router.post("/email-ingress/applicants", status_code=status.HTTP_204_NO_CONTENT)
async def applicants_email_webhook_handler(
    request: Request,
    envelope: str = Form(...),
    email: str = Form(...),
):
    ingress_record = WebhookValidator(request).validate_email_ingress_request(envelope)
    print(f"Processing email ingress for record {ingress_record}")
