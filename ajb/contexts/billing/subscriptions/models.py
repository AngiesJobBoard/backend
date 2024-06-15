from datetime import datetime
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


class CreateCompanySubscription(BaseModel):
    company_id: str
    plan: SubscriptionPlan
    start_date: datetime
    end_date: datetime | None = None
    stripe_subscription_id: str | None = None
    usage_cost_details: dict[UsageType, UsageDetail] = Field(
        default_factory=lambda: SUBSCRIPTION_USAGE_COST_DETAIL_DEFAULTS[
            SubscriptionPlan.STARTER
        ]
    )
    subscription_features: list[TierFeatures] = Field(
        default_factory=lambda: SUBSCRIPTION_FEATURE_DEFAULTS[SubscriptionPlan.STARTER]
    )
    pro_trial_expires: datetime | None = None

    @classmethod
    def get_default_subscription(cls, company_id: str) -> "CreateCompanySubscription":
        return cls(
            company_id=company_id,
            plan=SubscriptionPlan.STARTER,
            start_date=datetime.now(),
            usage_cost_details=SUBSCRIPTION_USAGE_COST_DETAIL_DEFAULTS[
                SubscriptionPlan.STARTER
            ],
            subscription_features=SUBSCRIPTION_FEATURE_DEFAULTS[
                SubscriptionPlan.STARTER
            ],
        )


class UserUpdateCompanySubscription(BaseModel):
    plan: SubscriptionPlan


class CompanySubscription(CreateCompanySubscription, BaseDataModel): ...
