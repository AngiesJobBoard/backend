from fastapi import APIRouter, status, Request

from ajb.base import RequestScope
from api.vendors import db


WEBHOOK_REQUEST_SCOPE = RequestScope(
    user_id="companies_webhook", db=db, company_id=None
)


router = APIRouter(
    tags=["Webhooks"],
    prefix="/webhooks/companies",
)


@router.post("/api-ingress/jobs", status_code=status.HTTP_204_NO_CONTENT)
async def jobs_api_webhook_handler(request: Request):
    print(request.__dict__)
    return {"message": "API request received successfully"}


@router.post("/api-ingress/applicants", status_code=status.HTTP_204_NO_CONTENT)
async def applicants_api_webhook_handler(request: Request):
    print(request.__dict__)
    return {"message": "API request received successfully"}


@router.post("/email-ingress/jobs", status_code=status.HTTP_204_NO_CONTENT)
async def jobs_email_webhook_handler(request: Request):
    print(request.__dict__)
    return {"message": "Email received successfully"}


@router.post("/email-ingress/applicants", status_code=status.HTTP_204_NO_CONTENT)
async def applicants_email_webhook_handler(request: Request):
    print(request.__dict__)
    return {"message": "Email received successfully"}
