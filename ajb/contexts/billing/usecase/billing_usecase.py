"""
If a user is on a free trial they will have a subscription object BUT with no stripe customer ID or anything.

When their trial expires they are asked to create a subscription
"""

from ajb.base import BaseUseCase, RequestScope, Collection
from ajb.contexts.billing.subscriptions.models import (
    CompanySubscription,
    SubscriptionPlan,
    UsageType,
)
from ajb.contexts.billing.usage.models import MonthlyUsage
from ajb.vendor.stripe.repository import (
    StripeRepository,
)
from ajb.vendor.stripe.models import (
    StripeCheckoutSessionCompleted,
    InvoicePaymentSucceeded,
)

from .start_create_subscription import StartCreateSubscription
from .complete_create_subscription import CompleteCreateSubscription
from .create_subscription_usage import CreateSubscriptionUsage
from .cancel_subscription import CancelSubscription
from .start_update_subscription import StartUpdateSubscription
from .complete_update_subscription import CompleteUpdateSubscription


class NoSubscriptionUsageAllottedException(Exception):
    pass


class CompanyBillingUsecase(BaseUseCase):
    def __init__(
        self, request_scope: RequestScope, stripe: StripeRepository | None = None
    ):
        super().__init__(request_scope)
        self.stripe = stripe or StripeRepository()

    def start_create_subscription(
        self, company_id: str, plan: SubscriptionPlan, appsumo_code: str | None
    ) -> CompanySubscription:
        """Initiated by user through the API - creates checkout session in stripe and attached subscription object to company pending the payment."""
        return StartCreateSubscription(
            self.request_scope, self.stripe
        ).start_create_subscription(company_id, plan, appsumo_code)

    def complete_create_subscription(self, data: StripeCheckoutSessionCompleted):
        """Webhook from Stripe - completes the subscription creation process after user completes checkout."""
        return CompleteCreateSubscription(
            self.request_scope, self.stripe
        ).complete_create_subscription(data)

    def create_company_usage(self, data: InvoicePaymentSucceeded):
        """
        This is a separate payment confirmation that comes with the checkout session.
        Getting this confirms the payment was successful and will allot usage on the platform for the associated company
        """
        CreateSubscriptionUsage(self.request_scope).create_usage_from_paid_invoice(data)

    def get_company_subscription(self, company_id: str) -> CompanySubscription:
        return self.get_repository(
            Collection.COMPANY_SUBSCRIPTIONS, self.request_scope, company_id
        ).get_sub_entity()

    def get_current_company_usage(self, company_id: str) -> MonthlyUsage:
        """Usage ID should be attached to current subscription object"""
        subscription: CompanySubscription = self.get_company_subscription(company_id)
        if subscription.current_usage_id is None:
            raise NoSubscriptionUsageAllottedException
        return self.get_object(
            Collection.COMPANY_SUBSCRIPTION_USAGE_AND_BILLING,
            subscription.current_usage_id,
        )

    def company_cancels_subscription(
        self, company_id: str, reason: str | None
    ) -> CompanySubscription:
        return CancelSubscription(
            self.request_scope, self.stripe
        ).cancel_company_subscription(company_id, reason)

    def company_starts_update_subscription(
        self, company_id: str, new_plan: SubscriptionPlan
    ):
        return StartUpdateSubscription(
            self.request_scope, self.stripe
        ).start_update_subscription(company_id, new_plan)

    def company_completes_update_subscription(self, data):
        return CompleteUpdateSubscription(
            self.request_scope, self.stripe
        ).complete_update_subscription(data)

    def increment_company_usage(
        self, company_id: str, usage_type: UsageType, amount_to_increment: int = 1
    ) -> None:
        """This assumes that the usage already exists. If there is no usage object the action should have failed already"""
        usage = self.get_current_company_usage(company_id)
        usage.transaction_counts[usage_type] += amount_to_increment
        self.get_repository(Collection.COMPANY_SUBSCRIPTION_USAGE_AND_BILLING).update(
            usage.id, usage
        )
