from fastapi import APIRouter, Request

from ajb.contexts.companies.email_ingress_webhooks.repository import CompanyEmailIngressRepository
from ajb.contexts.companies.email_ingress_webhooks.models import EmailIngressType, CompanyEmailIngress


router = APIRouter(tags=["Company Email Ingress"], prefix="/companies/{company_id}/jobs/{job_id}/email-ingress")


@router.get("/", response_model=CompanyEmailIngress)
def get_applicant_email_ingress(request: Request, company_id: str, job_id: str):
    return CompanyEmailIngressRepository(request.state.request_scope).get_one(
        company_id=company_id,
        job_id=job_id,
    )


@router.post("/enable", response_model=CompanyEmailIngress)
def enable_applicant_email_ingress(request: Request, company_id: str, job_id: str):
    repo = CompanyEmailIngressRepository(request.state.request_scope, company_id)
    record = repo.get_one(
        company_id=company_id,
        job_id=job_id,
        ingress_type=EmailIngressType.CREATE_APPLICATION.value
    )
    return repo.update_fields(
        record.id,
        is_active=True
    )


@router.post("/disable", response_model=CompanyEmailIngress)
def disable_applicant_email_ingress(request: Request, company_id: str, job_id: str):
    repo = CompanyEmailIngressRepository(request.state.request_scope, company_id)
    record = repo.get_one(
        company_id=company_id,
        job_id=job_id,
        ingress_type=EmailIngressType.CREATE_APPLICATION.value
    )
    return repo.update_fields(
        record.id,
        is_active=False
    )
