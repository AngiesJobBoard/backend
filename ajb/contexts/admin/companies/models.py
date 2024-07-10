from datetime import datetime
from pydantic import BaseModel
from ajb.contexts.billing.billing_models import SubscriptionPlan
from ajb.contexts.companies.models import UserCreateCompany


class AdminUserCreateSubscription(BaseModel):
    plan: SubscriptionPlan
    start_date: datetime | None = None
    end_date: datetime | None = None


class AdminUserCreateCompany(UserCreateCompany):
    owner_email: str
