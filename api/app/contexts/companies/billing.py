from fastapi import APIRouter, Request, Body

from ajb.contexts.billing.subscriptions.models import (
    UserUpdateCompanySubscription,
    CompanySubscription,
)
from ajb.contexts.billing.subscriptions.repository import CompanySubscriptionRepository
from ajb.contexts.billing.usecase import CompanyBillingUsecase
from ajb.contexts.billing.usage.repository import CompanySubscriptionUsageRepository
from ajb.contexts.billing.usage.models import MonthlyUsage
from ajb.contexts.billing.usecase.start_update_subscription import (
    CannotUpdateSubscriptionException,
    NoInitialSubscriptionException,
)

from api.middleware import scope
from api.exceptions import GenericHTTPException


router = APIRouter(tags=["Company Billing"], prefix="/companies/{company_id}")


@router.get("/subscription", response_model=CompanySubscription)
def get_subscription(request: Request, company_id: str):
    return CompanySubscriptionRepository(scope(request), company_id).get_sub_entity()


@router.post("/subscription", response_model=CompanySubscription)
def start_create_subscription(
    request: Request, company_id: str, subscription: UserUpdateCompanySubscription
):
    return CompanyBillingUsecase(scope(request)).start_create_subscription(
        company_id, subscription.plan, subscription.appsumo_code
    )


@router.post("/cancel-subscription", response_model=CompanySubscription)
def cancel_subscription(request: Request, company_id: str, reason: str = Body(...)):
    return CompanyBillingUsecase(scope(request)).company_cancels_subscription(
        company_id, reason
    )


@router.get("/current-usage", response_model=MonthlyUsage)
def get_current_usage(request: Request, company_id: str):
    return CompanyBillingUsecase(scope(request)).get_current_company_usage(company_id)


@router.post("/change-subscription", response_model=CompanySubscription)
def change_subscription(
    request: Request, company_id: str, subscription: UserUpdateCompanySubscription
):
    try:
        return CompanyBillingUsecase(scope(request)).company_starts_update_subscription(
            company_id, subscription.plan
        )
    except NoInitialSubscriptionException as e:
        raise GenericHTTPException(400, str(e))
    except CannotUpdateSubscriptionException as e:
        raise GenericHTTPException(400, str(e))


@router.get("/all-usages", response_model=list[MonthlyUsage])
def get_all_usages(request: Request, company_id: str):
    return CompanySubscriptionUsageRepository(scope(request), company_id).get_all(
        company_id=company_id
    )
