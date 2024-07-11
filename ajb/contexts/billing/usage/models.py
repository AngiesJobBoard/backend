"""
People have subscriptions in stripe and they get billed monthly.
When they first sign up they are billed immediately.

When billing occurs in stripe we will get a webhook sent to us with the billing details (success failure etc.)
As these events come in they should line up with this usage object which is a snapshot of the usage at the time of billing.
"""

from datetime import datetime
from pydantic import BaseModel, Field

from ajb.base import BaseDataModel
from ajb.vendor.stripe.models import InvoicePaymentSucceeded

from ..billing_models import UsageType


class CreateMonthlyUsage(BaseModel):
    company_id: str
    transaction_counts: dict[UsageType, int] = Field(
        default_factory=lambda: {
            UsageType.APPLICATIONS_PROCESSED: 0,
            UsageType.TOTAL_JOBS: 0,
            UsageType.TOTAL_RECRUITERS: 1,
        }
    )
    usage_expires: datetime | None
    invoice_details: InvoicePaymentSucceeded | None
    free_trial_usage: bool = False


class MonthlyUsage(BaseDataModel, CreateMonthlyUsage):
    pass
