from datetime import datetime
from pydantic import BaseModel
from ajb.contexts.billing.billing_models import SubscriptionPlan, TierFeatures, UsageDetail, UsageType
from ajb.contexts.billing.subscriptions.models import SubscriptionStatus
from ajb.contexts.companies.models import UserCreateCompany


class AdminUserCreateSubscription(BaseModel):
    plan: SubscriptionPlan
    end_date: datetime | None = None
    usage_cost_details: dict[UsageType, UsageDetail]
    subscription_features: list[TierFeatures]
    subscription_status: SubscriptionStatus


class AdminUserCreateCompany(UserCreateCompany):
    owner_email: str
