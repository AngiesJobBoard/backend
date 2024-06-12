import requests
from fastapi import APIRouter, status, Request, Form
from email import message_from_string

from ajb.base import RequestScope
from ajb.contexts.applications.usecase import ApplicationUseCase
from ajb.contexts.webhooks.ingress.jobs.usecase import WebhookJobsUseCase
from ajb.contexts.webhooks.ingress.applicants.usecase import WebhookApplicantsUseCase
from api.vendors import db, storage, kafka_producer

from api.open.middleware import OpenRequestValidator
from api.middleware import scope


WEBHOOK_REQUEST_SCOPE = RequestScope(
    user_id="companies_webhook", db=db, kafka=kafka_producer
)


router = APIRouter(
    tags=["Webhooks"],
    prefix="/webhooks/companies",
)


def temp_redirect_for_pcm(request: Request, payload: dict):
    requests.post(
        "https://api.angiesjobboard.com/webhooks/companies/api-ingress/applicants",
        headers=request.headers,
        json=payload,
    )


@router.post("/api-ingress/jobs", status_code=status.HTTP_204_NO_CONTENT)
async def jobs_api_webhook_handler(request: Request, payload: dict):
    request.state.request_scope = WEBHOOK_REQUEST_SCOPE
    ingress_record = OpenRequestValidator(request).validate_api_ingress_request()
    WebhookJobsUseCase(WEBHOOK_REQUEST_SCOPE).handle_webhook_event(
        ingress_record.company_id, payload  # type: ignore
    )
    return status.HTTP_204_NO_CONTENT


@router.post("/api-ingress/applicants", status_code=status.HTTP_204_NO_CONTENT)
async def applicants_api_webhook_handler(request: Request, payload: dict):
    new_location = "https://api.angiesjobboard.com/webhooks/companies/api-ingress/applicants"
    requests.post(
        new_location,
        headers=request.headers,
        json=payload,
    )
    return status.HTTP_204_NO_CONTENT

@router.post("/email-ingress", status_code=status.HTTP_204_NO_CONTENT)
async def jobs_email_webhook_handler(
    request: Request,
    envelope: str = Form(...),
    email: str = Form(...),
):
    request.state.request_scope = WEBHOOK_REQUEST_SCOPE
    # AJBTODO there is only handling for applicants coming in through email but jobs are technically also supported...
    ingress_record = OpenRequestValidator(request).validate_email_ingress_request(
        envelope
    )
    ingress_email = message_from_string(email)
    ApplicationUseCase(scope(request)).process_email_application_ingress(
        ingress_email, ingress_record
    )
    return status.HTTP_204_NO_CONTENT
