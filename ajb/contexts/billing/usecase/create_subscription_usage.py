"""
When a checkout session is completed it confirms the subscription.
And additional message is sent when the invoice is paid at the same time.

This is the message we care about for creating usage because we will expect this message once a month.
If it does not come in the next month (for whatever reason) then the current usage will automatically expire.
Usage is only created when this message is received from stripe.
"""

from datetime import datetime, timedelta

from ajb.base import BaseUseCase, Collection
from ajb.contexts.companies.models import Company
from ajb.contexts.billing.subscriptions.models import (
    CompanySubscription,
)
from ajb.contexts.billing.subscriptions.repository import CompanySubscriptionRepository
from ajb.contexts.billing.billing_audit_events.models import CreateAuditEvent
from ajb.contexts.billing.usage.models import CreateMonthlyUsage
from ajb.contexts.billing.usage.repository import CompanySubscriptionUsageRepository
from ajb.vendor.stripe.models import InvoicePaymentSucceeded


class InvoiceNotPaid(Exception):
    pass


class MismatchedSubscription(Exception):
    pass


class CreateSubscriptionUsage(BaseUseCase):
    def _store_raw_invoice_data(self, data: InvoicePaymentSucceeded) -> None:
        self.get_repository(Collection.BILLING_AUDIT_EVENTS).create(
            CreateAuditEvent(
                company_id=None, type="invoice_paid", data=data.model_dump()
            )
        )

    def validate_invoice(self, data: InvoicePaymentSucceeded) -> None:
        if data.paid is False or data.status != "paid":
            raise InvoiceNotPaid

    def create_usage_from_paid_invoice(self, data: InvoicePaymentSucceeded) -> None:
        self._store_raw_invoice_data(data)
        company: Company = self.get_repository(Collection.COMPANIES).get_one(
            stripe_customer_id=data.customer
        )
        subscription_repo = CompanySubscriptionRepository(
            self.request_scope, company.id
        )
        company_subscription = subscription_repo.get_sub_entity()
        self.validate_invoice(data)

        # All checks out, create the usage and attach created usage to subscription object
        created_usage = CompanySubscriptionUsageRepository(
            self.request_scope, company.id
        ).create(
            CreateMonthlyUsage(
                company_id=company.id,
                usage_expires=datetime.fromtimestamp(data.effective_at)
                + timedelta(days=40),  # ~1 month plus 10 day grace period
                invoice_details=data,
            )
        )
        company_subscription.current_usage_id = created_usage.id
        subscription_repo.set_sub_entity(company_subscription)
