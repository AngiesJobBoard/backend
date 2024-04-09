from datetime import datetime
from pydantic import BaseModel

from ajb.base import BaseDataModel

from ..billing_models import (
    SubscriptionPlan,
    UsageType,
    UsageDetail,
    SUBSCRIPTION_USAGE_COST_DETAIL_DEFAULTS,
)


class CreateCompanySubscription(BaseModel):
    company_id: str
    plan: SubscriptionPlan
    start_date: datetime
    end_date: datetime | None = None
    active: bool
    stripe_subscription_id: str | None = None
    usage_cost_details: dict[UsageType, UsageDetail]

    @classmethod
    def get_default_subscription(cls, company_id: str) -> "CreateCompanySubscription":
        return cls(
            company_id=company_id,
            plan=SubscriptionPlan.STARTER,
            start_date=datetime.now(),
            active=True,
            usage_cost_details=SUBSCRIPTION_USAGE_COST_DETAIL_DEFAULTS[
                SubscriptionPlan.STARTER
            ],
        )


class CompanySubscription(CreateCompanySubscription, BaseDataModel): ...
