from fastapi import APIRouter, Request

from ajb.contexts.billing.subscriptions.models import (
    UserUpdateCompanySubscription,
    CompanySubscription,
)
from ajb.contexts.billing.subscriptions.repository import CompanySubscriptionRepository
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
    return CompanyBillingUsecase(scope(request)).start_create_subscription(
        company_id, subscription.plan
    )


@router.get("/current-usage", response_model=MonthlyUsage)
def get_current_usage(request: Request, company_id: str):
    return CompanyBillingUsecase(scope(request)).get_current_company_usage(company_id)
