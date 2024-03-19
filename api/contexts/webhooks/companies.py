from fastapi import APIRouter, status, Request, Form
from email import message_from_string
from email.message import Message

from ajb.base import RequestScope
from ajb.contexts.applications.usecase import ApplicationUseCase
from ajb.contexts.resumes.models import UserCreateResume
from ajb.contexts.webhooks.jobs.models import JobsWebhook
from ajb.contexts.webhooks.jobs.usecase import WebhookJobsUseCase
from ajb.contexts.webhooks.applicants.models import ApplicantsWebhook
from ajb.contexts.webhooks.applicants.usecase import WebhookApplicantsUseCase
from ajb.contexts.companies.email_ingress_webhooks.models import CompanyEmailIngress
from api.vendors import db, storage

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
    WebhookJobsUseCase(WEBHOOK_REQUEST_SCOPE).handle_webhook_event(
        ingress_record.company_id, payload
    )
    return status.HTTP_204_NO_CONTENT


@router.post("/api-ingress/applicants", status_code=status.HTTP_204_NO_CONTENT)
async def applicants_api_webhook_handler(request: Request, payload: ApplicantsWebhook):
    ingress_record = WebhookValidator(request).validate_api_ingress_request()
    WebhookApplicantsUseCase(WEBHOOK_REQUEST_SCOPE).handle_webhook_event(
        ingress_record.company_id, payload
    )
    return status.HTTP_204_NO_CONTENT


def process_email_ingress(request_scope: RequestScope, ingress_email: Message, ingress_record: CompanyEmailIngress):
    application_usecase = ApplicationUseCase(request_scope, storage)

    if not ingress_email.is_multipart():
        raise ValueError("Email is not multipart")
    for part in ingress_email.walk():
        content_disposition = part.get("Content-Disposition")
        if not content_disposition or "attachment" not in content_disposition:
            continue
        if not ingress_record.job_id:
            continue
        application_usecase.create_application_from_resume(
            UserCreateResume(
                file_type=part.get_content_type(),
                file_name=str(part.get_filename()),
                resume_data=part.get_payload(decode=True),  # type: ignore
                company_id=ingress_record.company_id,
                job_id=ingress_record.job_id,
            )
        )


@router.post("/email-ingress", status_code=status.HTTP_204_NO_CONTENT)
async def jobs_email_webhook_handler(
    request: Request,
    envelope: str = Form(...),
    email: str = Form(...),
):
    ingress_record = WebhookValidator(request).validate_email_ingress_request(envelope)
    ingress_email = message_from_string(email)
    process_email_ingress(WEBHOOK_REQUEST_SCOPE, ingress_email, ingress_record)
    return status.HTTP_204_NO_CONTENT
