from enum import Enum
from datetime import datetime, timedelta
from pydantic import BaseModel

from ajb.base import BaseDataModel
from ajb.vendor.stripe.models import StripeCheckoutSessionCreated

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
    pending first payment means the user has not yet paid their first payment for the subscription
    Active means good financial standing.
    Inactive means the payments were past 10 days late and the subscription is set to inavtive
    Cancelled means the subscription was cancelled by the user
    Past Due means the subscription is past due between 0 and 10 days
    Trialing means the subscription is in the pro trial
    App Sumo is a special status for App Sumo users who have a single payment - lifetime access deal
    """

    PENDING_FIRST_PAYMENT = "pending_first_payment"
    PENDING_UPDATE_PAYMENT = "pending_update_payment"
    ACTIVE = "active"
    INACTIVE = "inactive"
    CANCELLED = "cancelled"
    PAST_DUE = "past_due"


class CreateCompanySubscription(BaseModel):
    company_id: str
    plan: SubscriptionPlan
    start_date: datetime
    end_date: datetime | None = None
    stripe_customer_id: str | None = None  # Only none if plan type is free trial
    stripe_subscription_id: str | None = None
    usage_cost_details: dict[UsageType, UsageDetail]
    subscription_features: list[TierFeatures]
    subscription_status: SubscriptionStatus
    checkout_session: StripeCheckoutSessionCreated | None
    current_usage_id: str | None = None
    free_trial_ends: datetime | None = None

    @classmethod
    def create_trial_subscription(
        cls, company_id: str, usage_id: str
    ) -> "CreateCompanySubscription":
        return cls(
            company_id=company_id,
            plan=SubscriptionPlan.GOLD_TRIAL,
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=14),
            usage_cost_details=SUBSCRIPTION_USAGE_COST_DETAIL_DEFAULTS[
                SubscriptionPlan.GOLD
            ],
            subscription_features=SUBSCRIPTION_FEATURE_DEFAULTS[SubscriptionPlan.GOLD],
            subscription_status=SubscriptionStatus.ACTIVE,
            checkout_session=None,
            current_usage_id=usage_id,
            free_trial_ends=datetime.now() + timedelta(days=14),
        )

    @classmethod
    def create_app_sumo_subscription(
        cls, company_id: str, usage_id: str
    ) -> "CreateCompanySubscription":
        return cls(
            company_id=company_id,
            plan=SubscriptionPlan.APPSUMO,
            start_date=datetime.now(),
            end_date=None,
            usage_cost_details=SUBSCRIPTION_USAGE_COST_DETAIL_DEFAULTS[
                SubscriptionPlan.APPSUMO
            ],
            subscription_features=SUBSCRIPTION_FEATURE_DEFAULTS[
                SubscriptionPlan.APPSUMO
            ],
            subscription_status=SubscriptionStatus.ACTIVE,
            checkout_session=None,
            current_usage_id=usage_id,
        )

    @classmethod
    def create_subscription(
        cls,
        company_id: str,
        stripe_customer_id: str,
        plan: SubscriptionPlan,
        checkout_session: StripeCheckoutSessionCreated,
    ) -> "CreateCompanySubscription":
        return cls(
            company_id=company_id,
            plan=plan,
            start_date=datetime.now(),
            end_date=None,
            stripe_customer_id=stripe_customer_id,
            usage_cost_details=SUBSCRIPTION_USAGE_COST_DETAIL_DEFAULTS[plan],
            subscription_features=SUBSCRIPTION_FEATURE_DEFAULTS[plan],
            subscription_status=SubscriptionStatus.PENDING_FIRST_PAYMENT,
            checkout_session=checkout_session,
        )


class UserUpdateCompanySubscription(BaseModel):
    plan: SubscriptionPlan
    appsumo_code: str | None = None


class CompanySubscription(CreateCompanySubscription, BaseDataModel):

    def update_to_new_subscription(
        self, new_plan: SubscriptionPlan, new_stripe_subscription_id: str
    ):
        self.plan = new_plan
        self.stripe_subscription_id = new_stripe_subscription_id
        self.subscription_status = SubscriptionStatus.PENDING_UPDATE_PAYMENT
        self.checkout_session = None
        self.usage_cost_details = SUBSCRIPTION_USAGE_COST_DETAIL_DEFAULTS[new_plan]
        self.subscription_features = SUBSCRIPTION_FEATURE_DEFAULTS[new_plan]
