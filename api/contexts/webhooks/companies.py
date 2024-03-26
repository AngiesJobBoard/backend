from fastapi import APIRouter, status, Request, Form
from email import message_from_string
from email.message import Message

from ajb.base import RequestScope
from ajb.contexts.applications.usecase import ApplicationUseCase
from ajb.contexts.resumes.models import UserCreateResume
from ajb.contexts.webhooks.ingress.jobs.models import JobsWebhook, JobWebhookEventType
from ajb.contexts.webhooks.ingress.jobs.usecase import WebhookJobsUseCase
from ajb.contexts.webhooks.ingress.applicants.models import (
    ApplicantsWebhook,
    ApplicantWebhookEventType,
)
from ajb.contexts.webhooks.ingress.applicants.usecase import WebhookApplicantsUseCase
from ajb.contexts.companies.email_ingress_webhooks.models import CompanyEmailIngress
from api.vendors import db, storage, mixpanel

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
    if payload.type == JobWebhookEventType.CREATE:
        mixpanel.job_created_from_api_webhook_ingress(
            WEBHOOK_REQUEST_SCOPE.user_id,
            ingress_record.company_id,
            payload.data.get("external_reference_code"),
        )
    return status.HTTP_204_NO_CONTENT


@router.post("/api-ingress/applicants", status_code=status.HTTP_204_NO_CONTENT)
async def applicants_api_webhook_handler(request: Request, payload: ApplicantsWebhook):
    ingress_record = WebhookValidator(request).validate_api_ingress_request()
    applicant_result = WebhookApplicantsUseCase(
        WEBHOOK_REQUEST_SCOPE
    ).handle_webhook_event(ingress_record.company_id, payload)
    if payload.type == ApplicantWebhookEventType.CREATE:
        mixpanel.application_created_from_api_webhook_ingress(
            WEBHOOK_REQUEST_SCOPE.user_id,
            ingress_record.company_id,
            payload.data.get("external_job_reference_code"),
            applicant_result.id,
        )
    return status.HTTP_204_NO_CONTENT


def process_email_ingress(
    request_scope: RequestScope,
    ingress_email: Message,
    ingress_record: CompanyEmailIngress,
):
    request_scope.company_id = ingress_record.company_id
    application_usecase = ApplicationUseCase(request_scope, storage)

    if not ingress_email.is_multipart():
        raise ValueError("Email is not multipart")
    for part in ingress_email.walk():
        content_disposition = part.get("Content-Disposition")
        if not content_disposition or "attachment" not in content_disposition:
            continue
        if not ingress_record.job_id:
            continue
        created_application = application_usecase.create_application_from_resume(
            UserCreateResume(
                file_type=part.get_content_type(),
                file_name=str(part.get_filename()),
                resume_data=part.get_payload(decode=True),  # type: ignore
                company_id=ingress_record.company_id,
                job_id=ingress_record.job_id,
            )
        )
        mixpanel.application_created_from_email_ingress(
            request_scope.user_id,
            ingress_record.company_id,
            ingress_record.job_id,
            created_application.id,
        )


@router.post("/email-ingress", status_code=status.HTTP_204_NO_CONTENT)
async def jobs_email_webhook_handler(
    request: Request,
    envelope: str = Form(...),
    email: str = Form(...),
):
    # AJBTODO there is only handling for applicants coming in through email but jobs are technically also supported...
    ingress_record = WebhookValidator(request).validate_email_ingress_request(envelope)
    ingress_email = message_from_string(email)
    process_email_ingress(WEBHOOK_REQUEST_SCOPE, ingress_email, ingress_record)
    return status.HTTP_204_NO_CONTENT
