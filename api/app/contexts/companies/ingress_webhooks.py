from fastapi import APIRouter, Request, Depends

from ajb.base import QueryFilterParams, build_pagination_response
from ajb.contexts.companies.api_ingress_webhooks.models import (
    CreateCompanyAPIIngress,
    UserCreateIngress,
    CompanyAPIIngress,
    PaginatedCompanyIngress,
)
from ajb.contexts.companies.api_ingress_webhooks.repository import (
    CompanyAPIIngressRepository,
)
from ajb.contexts.companies.api_ingress_webhooks.usecase import APIIngressUsecase
from api.middleware import scope

router = APIRouter(
    tags=["Company API Ingress Webhooks"],
    prefix="/companies/{company_id}/api-ingress-webhooks",
)


@router.get("/", response_model=PaginatedCompanyIngress)
def get_all_company_ingress_webhooks(
    request: Request,
    company_id: str,
    job_id: str | None = None,
    query: QueryFilterParams = Depends(),
):
    response = APIIngressUsecase(scope(request)).get_ingress_records_with_count(
        company_id, job_id, query
    )
    return build_pagination_response(
        response,
        query.page,
        query.page_size,
        request.url._url,
        PaginatedCompanyIngress,
    )


@router.post("/", response_model=CompanyAPIIngress)
def create_company_egress_webhook(
    request: Request, company_id: str, webhook: UserCreateIngress
):
    return CompanyAPIIngressRepository(scope(request), company_id).create(
        CreateCompanyAPIIngress.generate(
            company_id,
            webhook.integration_name,
            webhook.source_type,
            webhook.source,
            is_active=True,
        )
    )


@router.get("/{webhook_id}", response_model=CompanyAPIIngress)
def get_company_egress_webhook(request: Request, company_id: str, webhook_id: str):
    return CompanyAPIIngressRepository(scope(request), company_id).get(webhook_id)


@router.patch("/{webhook_id}/disable", response_model=CompanyAPIIngress)
def disable_company_egress_webhook(request: Request, company_id: str, webhook_id: str):
    return CompanyAPIIngressRepository(scope(request), company_id).update_fields(
        webhook_id, is_active=False
    )


@router.patch("/{webhook_id}/enable", response_model=CompanyAPIIngress)
def enable_company_egress_webhook(request: Request, company_id: str, webhook_id: str):
    return CompanyAPIIngressRepository(scope(request), company_id).update_fields(
        webhook_id, is_active=True
    )


@router.delete("/{webhook_id}")
def delete_company_egress_webhook(request: Request, company_id: str, webhook_id: str):
    return CompanyAPIIngressRepository(scope(request), company_id).delete(webhook_id)
