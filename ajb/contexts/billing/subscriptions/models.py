from enum import Enum
from datetime import datetime, timedelta
from pydantic import BaseModel, Field

from ajb.base import BaseDataModel

from ..billing_models import (
    SubscriptionPlan,
    UsageType,
    UsageDetail,
    TierFeatures,
    SUBSCRIPTION_USAGE_COST_DETAIL_DEFAULTS,
    SUBSCRIPTION_FEATURE_DEFAULTS,
)


class SubscriptionStatus(str, Enum):
    """
    More details about each status:
    Active means good financial standing.
    Inactive means the payments were past 10 days late and the subscription is set to inavtive
    Cancelled means the subscription was cancelled by the user
    Past Due means the subscription is past due between 0 and 10 days
    Trialing means the subscription is in the pro trial
    App Sumo is a special status for App Sumo users who have a single payment - lifetime access deal
    """

    ACTIVE = "active"
    INACTIVE = "inactive"
    CANCELLED = "cancelled"
    PAST_DUE = "past_due"
    TRIALING = "trialing"
    APP_SUMO = "app_sumo"


class CreateCompanySubscription(BaseModel):
    company_id: str
    plan: SubscriptionPlan
    start_date: datetime
    end_date: datetime | None = None
    stripe_customer_id: str | None = None
    stripe_subscription_id: str | None = None
    usage_cost_details: dict[UsageType, UsageDetail]
    subscription_features: list[TierFeatures]
    pro_trial_expires: datetime | None = None
    subscription_status: SubscriptionStatus

    @classmethod
    def create_trial_subscription(cls, company_id: str) -> "CreateCompanySubscription":
        return cls(
            company_id=company_id,
            plan=SubscriptionPlan.GOLD,
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=14),
            usage_cost_details=SUBSCRIPTION_USAGE_COST_DETAIL_DEFAULTS[
                SubscriptionPlan.GOLD
            ],
            subscription_features=SUBSCRIPTION_FEATURE_DEFAULTS[SubscriptionPlan.GOLD],
            pro_trial_expires=datetime.now() + timedelta(days=14),
            subscription_status=SubscriptionStatus.TRIALING,
        )

    @classmethod
    def create_app_sumo_subscription(
        cls, company_id: str, stripe_customer_id: str
    ) -> "CreateCompanySubscription":
        return cls(
            company_id=company_id,
            plan=SubscriptionPlan.APPSUMO,
            start_date=datetime.now(),
            end_date=None,
            stripe_customer_id=stripe_customer_id,
            usage_cost_details=SUBSCRIPTION_USAGE_COST_DETAIL_DEFAULTS[
                SubscriptionPlan.APPSUMO
            ],
            subscription_features=SUBSCRIPTION_FEATURE_DEFAULTS[
                SubscriptionPlan.APPSUMO
            ],
            pro_trial_expires=None,
            subscription_status=SubscriptionStatus.APP_SUMO,
        )

    @classmethod
    def create_subscription(
        cls,
        company_id: str,
        stripe_customer_id: str,
        stripe_subscription_id: str,
        plan: SubscriptionPlan,
    ) -> "CreateCompanySubscription":
        return cls(
            company_id=company_id,
            plan=plan,
            start_date=datetime.now(),
            end_date=None,
            stripe_customer_id=stripe_customer_id,
            stripe_subscription_id=stripe_subscription_id,
            usage_cost_details=SUBSCRIPTION_USAGE_COST_DETAIL_DEFAULTS[plan],
            subscription_features=SUBSCRIPTION_FEATURE_DEFAULTS[plan],
            pro_trial_expires=None,
            subscription_status=SubscriptionStatus.ACTIVE,
        )


class UserUpdateCompanySubscription(BaseModel):
    plan: SubscriptionPlan


class CompanySubscription(CreateCompanySubscription, BaseDataModel): ...
