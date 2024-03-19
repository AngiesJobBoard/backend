from fastapi import APIRouter, status, Request, Form
from email import message_from_string

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
    ingress_record = WebhookValidator(request).validate_api_ingress_request()
    WebhookJobsUseCase(WEBHOOK_REQUEST_SCOPE).handle_webhook_event(ingress_record.company_id, payload)
    return status.HTTP_204_NO_CONTENT


@router.post("/api-ingress/applicants", status_code=status.HTTP_204_NO_CONTENT)
async def applicants_api_webhook_handler(request: Request, payload: ApplicantsWebhook):
    ingress_record = WebhookValidator(request).validate_api_ingress_request()
    WebhookApplicantsUseCase(WEBHOOK_REQUEST_SCOPE).handle_webhook_event(ingress_record.company_id, payload)
    return status.HTTP_204_NO_CONTENT


@router.post("/email-ingress", status_code=status.HTTP_204_NO_CONTENT)
async def jobs_email_webhook_handler(
    request: Request,
    envelope: str = Form(...),
    email: str = Form(...),
):
    ingress_record = WebhookValidator(request).validate_email_ingress_request(envelope)
    ingress_email = message_from_string(email)
    if ingress_email.is_multipart():
        for part in ingress_email.walk():
            content_type = part.get_content_type()
            content_disposition = part.get("Content-Disposition")
            if content_type == "text/plain" and content_disposition is None:
                body = part.get_payload(decode=True)
    else:
        body = ingress_email.get_payload(decode=True)
    print(f"Processing email ingress for record {ingress_record}")
    print(body)
    return status.HTTP_204_NO_CONTENT
