from datetime import datetime
from pydantic import BaseModel

from ajb.base import BaseDataModel

from ..billing_models import SubscriptionPlan, CompanyFreeTier, CompanyRates


class CreateCompanySubscription(BaseModel):
    company_id: str
    plan: SubscriptionPlan
    start_date: datetime
    end_date: datetime | None = None
    active: bool
    stripe_subscription_id: str
    rates: CompanyRates
    free_tier: CompanyFreeTier


class CompanySubscription(CreateCompanySubscription, BaseDataModel): ...
