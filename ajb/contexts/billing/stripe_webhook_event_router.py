"""
This module helps to route different messages posted to us from stripe to the correct event handler.
"""

from enum import Enum

from ajb.base import RequestScope
from ajb.contexts.billing.usecase import CompanyBillingUsecase
from ajb.vendor.stripe.models import (
    StripeCheckoutSessionCompleted,
    InvoicePaymentSucceeded,
)
from ajb.vendor.stripe.repository import StripeRepository


class StripeEventType(str, Enum):
    CHECKOUT_SESSION_COMPLETED = "checkout.session.completed"
    INVOICE_PAYMENT_SUCCEEDED = "invoice.payment_succeeded"
    INVOICE_PAYMENT_FAILED = "invoice.payment_failed"
    CHARGE_SUCCEEDED = "charge.succeeded"


class StripeWebhookEventRouter:
    def __init__(
        self,
        request_scope: RequestScope,
        payload: dict,
        stripe: StripeRepository | None = None,
    ):
        self.request_scope = request_scope
        self.payload = payload
        self.stripe = stripe or StripeRepository()

    def handle_complete_subscription_setup(self) -> None:
        """Comes from the checkout session complete event"""
        CompanyBillingUsecase(
            self.request_scope, self.stripe
        ).complete_create_subscription(
            StripeCheckoutSessionCompleted(**self.payload["data"]["object"])
        )

    def handle_invoice_payment_succeeded(self) -> None:
        """
        Comes from the invoice payment succeeded event.
        We need to discern between the two types of events for create or update subscription invoice charges
        """
        usecase = CompanyBillingUsecase(self.request_scope, self.stripe)
        structured_data = InvoicePaymentSucceeded(**self.payload["data"]["object"])
        if structured_data.billing_reason == "subscription_update":
            return usecase.company_completes_update_subscription(structured_data)
        elif structured_data.billing_reason == "subscription_create":
            return usecase.create_company_usage(structured_data)
        raise ValueError("Unknown billing reason")

    def handle_invoice_payment_failed(self) -> None:
        raise NotImplementedError("Invoice payment failed event not implemented")

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
