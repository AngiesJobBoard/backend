from fastapi import APIRouter, Request

from ajb.contexts.billing.subscriptions.models import (
    UserUpdateCompanySubscription,
    CompanySubscription,
)
from ajb.contexts.billing.subscriptions.repository import CompanySubscriptionRepository
from ajb.contexts.billing.usecase.start_create_subscription import (
    StartCreateSubscription,
)
from ajb.contexts.billing.usecase import CompanyBillingUsecase
from ajb.contexts.billing.usage.models import MonthlyUsage
from api.middleware import scope


router = APIRouter(tags=["Company Billing"], prefix="/companies/{company_id}")


@router.get("/subscription", response_model=CompanySubscription)
def get_subscription(request: Request, company_id: str):
    return CompanySubscriptionRepository(scope(request), company_id).get_sub_entity()


@router.post("/subscription", response_model=CompanySubscription)
def start_create_subscription(
    request: Request, company_id: str, subscription: UserUpdateCompanySubscription
):
    return StartCreateSubscription(scope(request)).start_create_subscription(
        company_id, subscription.plan
    )


@router.get("/current-usage", response_model=MonthlyUsage)
def get_current_usage(
    request: Request, company_id: str, billing_period: str | None = None
):
    return CompanyBillingUsecase(scope(request)).get_or_create_company_usage(
        company_id, billing_period
    )


@router.get("/usage-history", response_model=tuple[list[MonthlyUsage], int])
def get_usage_history(
    request: Request, company_id: str, page: int = 0, page_size: int = 10
):
    return CompanyBillingUsecase(scope(request)).get_historic_company_usage(
        company_id, page, page_size
    )
