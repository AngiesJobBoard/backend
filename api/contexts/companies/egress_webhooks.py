from fastapi import APIRouter, Request, Depends

from ajb.base import QueryFilterParams, build_pagination_response
from ajb.contexts.companies.api_egress_webhooks.models import (
    UserCreateCompanyAPIEgress,
    CreateCompanyAPIEgress,
    CompanyAPIEgress,
    PaginatedCompanyEgressWebhooks,
    UpdateCompanyAPIEgress,
)
from ajb.contexts.companies.api_egress_webhooks.repository import (
    CompanyAPIEgressRepository,
)


router = APIRouter(
    tags=["Company API Egress Webhooks"],
    prefix="/companies/{company_id}/api-egress-webhooks",
)


@router.get("/", response_model=PaginatedCompanyEgressWebhooks)
def get_all_company_egress_webhooks(
    request: Request, company_id: str, query: QueryFilterParams = Depends()
):
    response = CompanyAPIEgressRepository(
        request.state.request_scope, company_id
    ).query(query)
    return build_pagination_response(
        response,
        query.page,
        query.page_size,
        request.url._url,
        PaginatedCompanyEgressWebhooks,
    )


@router.post("/", response_model=CompanyAPIEgress)
def create_company_egress_webhook(
    request: Request, company_id: str, webhook: UserCreateCompanyAPIEgress
):
    return CompanyAPIEgressRepository(request.state.request_scope, company_id).create(
        CreateCompanyAPIEgress(**webhook.model_dump(), company_id=company_id)
    )


@router.get("/{webhook_id}", response_model=CompanyAPIEgress)
def get_company_egress_webhook(request: Request, company_id: str, webhook_id: str):
    return CompanyAPIEgressRepository(request.state.request_scope, company_id).get(
        webhook_id
    )


@router.patch("/{webhook_id}/disable", response_model=CompanyAPIEgress)
def disable_company_egress_webhook(request: Request, company_id: str, webhook_id: str):
    return CompanyAPIEgressRepository(
        request.state.request_scope, company_id
    ).update_fields(webhook_id, is_active=False)


@router.patch("/{webhook_id}/enable", response_model=CompanyAPIEgress)
def enable_company_egress_webhook(request: Request, company_id: str, webhook_id: str):
    return CompanyAPIEgressRepository(
        request.state.request_scope, company_id
    ).update_fields(webhook_id, is_active=True)


@router.put("/{webhook_id}", response_model=CompanyAPIEgress)
def update_company_egress_webhook(
    request: Request, company_id: str, webhook_id: str, webhook: UpdateCompanyAPIEgress
):
    return CompanyAPIEgressRepository(request.state.request_scope, company_id).update(
        webhook_id, webhook
    )


@router.delete("/{webhook_id}")
def delete_company_egress_webhook(request: Request, company_id: str, webhook_id: str):
    return CompanyAPIEgressRepository(request.state.request_scope, company_id).delete(
        webhook_id
    )
