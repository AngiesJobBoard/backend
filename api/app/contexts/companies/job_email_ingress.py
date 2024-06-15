from fastapi import APIRouter, Request

from ajb.contexts.companies.email_ingress_webhooks.repository import (
    CompanyEmailIngressRepository,
)
from ajb.contexts.companies.email_ingress_webhooks.models import (
    EmailIngressType,
    CompanyEmailIngress,
)
from ajb.contexts.billing.validate_usage import (
    BillingValidateUsageUseCase,
    TierFeatures,
    FeatureNotAvailableOnTier,
)
from api.exceptions import FeatureNotAvailableOnTierHTTPException
from api.middleware import scope


router = APIRouter(
    tags=["Company Email Ingress"],
    prefix="/companies/{company_id}/jobs/{job_id}/email-ingress",
)


@router.get("/", response_model=CompanyEmailIngress)
def get_applicant_email_ingress(request: Request, company_id: str, job_id: str):
    return CompanyEmailIngressRepository(scope(request)).get_one(
        company_id=company_id,
        job_id=job_id,
    )


def check_ingress_feature(request_scope, company_id: str):
    try:
        BillingValidateUsageUseCase(request_scope, company_id).validate_feature_access(
            TierFeatures.EMAIL_INGRESS
        )
    except FeatureNotAvailableOnTier:
        raise FeatureNotAvailableOnTierHTTPException


def enable_ingress_feature(request_scope, company_id: str, job_id: str):
    repo = CompanyEmailIngressRepository(request_scope, company_id)
    record = repo.get_one(
        company_id=company_id,
        job_id=job_id,
        ingress_type=EmailIngressType.CREATE_APPLICATION.value,
    )
    return repo.update_fields(record.id, is_active=True)


@router.post("/enable", response_model=CompanyEmailIngress)
def enable_applicant_email_ingress(request: Request, company_id: str, job_id: str):
    check_ingress_feature(scope(request), company_id)
    return enable_ingress_feature(scope(request), company_id, job_id)


@router.post("/disable", response_model=CompanyEmailIngress)
def disable_applicant_email_ingress(request: Request, company_id: str, job_id: str):
    repo = CompanyEmailIngressRepository(scope(request), company_id)
    record = repo.get_one(
        company_id=company_id,
        job_id=job_id,
        ingress_type=EmailIngressType.CREATE_APPLICATION.value,
    )
    return repo.update_fields(record.id, is_active=False)
