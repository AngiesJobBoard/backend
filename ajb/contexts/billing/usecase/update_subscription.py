"""
This module handles the business action of changing a users subscription plan

Whether increasing or decreasing, the usage is carried over, the limits set to the new plan, and the expiry updated

There is no extra checkout screen needed, just update the subscriptin in stripe and handle updating the usage object

say right now is 50 bucks a month and its halfway through, they want to upgrade to 100 bucks a month
so they are set up with a new subscription that has been prorated for 25 bucks and the usage is updated to the new plan

if they are at 100 dollars a month and want to downgrade to 50, they are set up with a new subscription that is prorated for 50 bucks and the usage is updated to the new plan
if the prorated amount is less than the amount already paid, then there is no immediate charge.

"""
from datetime import datetime, timedelta

from ajb.base import BaseUseCase, Collection
from ajb.contexts.companies.models import Company
from ajb.contexts.billing.subscriptions.repository import CompanySubscriptionRepository
from ajb.contexts.billing.billing_audit_events.models import CreateAuditEvent
from ajb.contexts.billing.usage.models import CreateMonthlyUsage
from ajb.contexts.billing.usage.repository import CompanySubscriptionUsageRepository
from ajb.vendor.stripe.models import InvoicePaymentSucceeded


class CreateSubscriptionUsage(BaseUseCase):
    def _store_raw_invoice_data(self, data: InvoicePaymentSucceeded) -> None:
        self.get_repository(Collection.BILLING_AUDIT_EVENTS).create(
            CreateAuditEvent(
                company_id=None, type="subscription_update_invoice_paid", data=data.model_dump()
            )
        )

    def create_usage_from_paid_invoice(self, data: InvoicePaymentSucceeded) -> None:
        self._store_raw_invoice_data(data)
        company: Company = self.get_repository(Collection.COMPANIES).get_one(
            stripe_customer_id=data.customer
        )
        subscription_repo = CompanySubscriptionRepository(
            self.request_scope, company.id
        )
        company_subscription = subscription_repo.get_sub_entity()

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
