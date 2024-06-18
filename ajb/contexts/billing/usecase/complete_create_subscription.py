"""
This module contains the business action for complete the create subscription work flow
This is initated by a POST request the stripe sends us after a user completes their checkout session successfully.
"""

from ajb.base import BaseUseCase, Collection, RequestScope
from ajb.contexts.companies.models import Company
from ajb.contexts.billing.subscriptions.models import (
    SubscriptionStatus,
    CompanySubscription,
)
from ajb.contexts.billing.subscriptions.repository import CompanySubscriptionRepository
from ajb.contexts.billing.billing_audit_events.models import CreateAuditEvent
from ajb.vendor.stripe.repository import StripeRepository
from ajb.vendor.stripe.models import StripeCheckoutSessionCompleted


class NoCheckoutSessionSaved(Exception):
    pass


class CheckoutSessionIdMismatch(Exception):
    pass


class PaymentStatusNotPaid(Exception):
    pass


class CheckoutSessionStatusNotComplete(Exception):
    pass


class CompleteCreateSubscription(BaseUseCase):
    def __init__(
        self, request_scope: RequestScope, stripe: StripeRepository | None = None
    ):
        super().__init__(request_scope)
        self.stripe = stripe or StripeRepository()

    def _store_raw_checkout_session_data(
        self, data: StripeCheckoutSessionCompleted
    ) -> None:
        self.get_repository(Collection.BILLING_AUDIT_EVENTS).create(
            CreateAuditEvent(
                company_id=None,
                type="stripe_checkout_session_completed",
                data=data.model_dump(),
            )
        )

    def validate_session(
        self, subscription: CompanySubscription, data: StripeCheckoutSessionCompleted
    ) -> None:
        if subscription.checkout_session is None:
            raise NoCheckoutSessionSaved()

        if subscription.checkout_session.id != data.id:
            raise CheckoutSessionIdMismatch()

        if data.payment_status != "paid":
            raise PaymentStatusNotPaid()

        if data.status != "complete":
            raise CheckoutSessionStatusNotComplete()

    def complete_create_subscription(
        self, data: StripeCheckoutSessionCompleted
    ) -> None:
        self._store_raw_checkout_session_data(data)
        company: Company = self.get_repository(Collection.COMPANIES).get_one(
            stripe_customer_id=data.customer
        )
        subscription_repo = CompanySubscriptionRepository(
            self.request_scope, company.id
        )
        company_subscription = subscription_repo.get_sub_entity()
        self.validate_session(company_subscription, data)
        subscription_repo.update_fields(
            company_subscription.id,
            stripe_subscription_id=data.subscription,  # Will remain None for app sumo single payments
            subscription_status=SubscriptionStatus.ACTIVE,
        )
