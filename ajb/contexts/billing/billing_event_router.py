"""
This module helps to route different messages posted to us from stripe to the correct event handler.
"""

from enum import Enum

from ajb.base import RequestScope
from ajb.contexts.billing.usecase.complete_create_subscription import (
    CompleteCreateSubscription,
)
from ajb.contexts.billing.usecase.subscription_payment_success import (
    SubscriptionPaymentSuccess,
)
from ajb.contexts.billing.usecase.subscription_payment_failure import (
    SubscriptionPaymentFailure,
)
from ajb.vendor.stripe.models import (
    StripeCheckoutSessionCompleted,
    InvoicePaymentSucceeded,
    InvoicePaymentFailed,
)


class StripeEventType(str, Enum):
    CHECKOUT_SESSION_COMPLETED = "checkout.session.completed"
    INVOICE_PAYMENT_SUCCEEDED = "invoice.payment_succeeded"
    INVOICE_PAYMENT_FAILED = "invoice.payment_failed"


class StripeBillingEventRouter:
    def __init__(self, request_scope: RequestScope, payload: dict):
        self.request_scope = request_scope
        self.payload = payload

    def handle_complete_subscription_setup(self) -> None:
        CompleteCreateSubscription(self.request_scope).complete_subscription_setup(
            data=StripeCheckoutSessionCompleted(**self.payload["data"]["object"])
        )

    def handle_invoice_payment_succeeded(self) -> None:
        SubscriptionPaymentSuccess(self.request_scope).update_company_usage(
            InvoicePaymentSucceeded(**self.payload["data"]["object"])
        )

    def handle_invoice_payment_failed(self) -> None:
        SubscriptionPaymentFailure(self.request_scope).update_company_usage(
            InvoicePaymentFailed(**self.payload["data"]["object"])
        )

    def route_event(self) -> None:
        """
        There is an attribute 'type' on every payload from stripe that tells us what type of event it is.
        Use this to map it to a function that will handle the event.
        """
        ROUTER_MAP = {
            StripeEventType.CHECKOUT_SESSION_COMPLETED: self.handle_complete_subscription_setup,
            StripeEventType.INVOICE_PAYMENT_SUCCEEDED: self.handle_invoice_payment_succeeded,
            StripeEventType.INVOICE_PAYMENT_FAILED: self.handle_invoice_payment_failed,
        }
        ROUTER_MAP[StripeEventType(self.payload["type"])]()
