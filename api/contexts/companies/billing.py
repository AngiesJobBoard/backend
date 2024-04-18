from fastapi import APIRouter, Request

from ajb.contexts.billing.subscriptions.models import (
    UserUpdateCompanySubscription,
    CompanySubscription,
)
from ajb.contexts.billing.usecase import CompanyBillingUsecase
from ajb.contexts.billing.usage.models import MonthlyUsage


router = APIRouter(tags=["Company Billing"], prefix="/companies/{company_id}")


@router.get("/subscription", response_model=CompanySubscription)
def get_subscription(request: Request, company_id: str):
    return CompanyBillingUsecase(
        request.state.request_scope
    ).get_or_create_company_subscription(company_id)


@router.patch("/subscription")
def update_subscription(
    request: Request, company_id: str, updates: UserUpdateCompanySubscription
):
    return CompanyBillingUsecase(
        request.state.request_scope
    ).update_company_subscription(company_id, updates)


@router.get("/current-usage", response_model=MonthlyUsage)
def get_current_usage(request: Request, company_id: str, billing_period: str | None = None):
    return CompanyBillingUsecase(
        request.state.request_scope
    ).get_or_create_company_usage(company_id, billing_period)


@router.get("/usage-history", response_model=tuple[list[MonthlyUsage], int])
def get_usage_history(
    request: Request, company_id: str, page: int = 0, page_size: int = 10
):
    return CompanyBillingUsecase(
        request.state.request_scope
    ).get_historic_company_usage(company_id, page, page_size)
