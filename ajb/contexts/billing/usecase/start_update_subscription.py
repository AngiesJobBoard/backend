"""
This module handles the business action of starting to change a users subscription plan.
It is a mirror of creating a subscription where it begins with setting up the new subscription object but it is not confirmed yet.

Stripe will process the prorated amount depending on the time in the current billing period and the cost of the new plan.
Once processed, we will received an invoice.payment_succeeded event from stripe.
It will confirm and activate the company's subscription and their usage

"""

from ajb.base import BaseUseCase, Collection, RequestScope
from ajb.contexts.billing.subscriptions.repository import CompanySubscriptionRepository
from ajb.contexts.billing.billing_audit_events.models import CreateAuditEvent
from ajb.vendor.stripe.models import InvoicePaymentSucceeded
from ajb.vendor.stripe.repository import StripeRepository
from ajb.contexts.billing.subscriptions.models import (
    SubscriptionPlan,
    CompanySubscription,
)

from .SUBSCRIPTION_PRICE_MAP import SUBSCRIPTION_PRICE_MAP


class NoInitialSubscriptionException(Exception):
    pass


class CannotUpdateSubscriptionException(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class BadSubscriptionChange(Exception):
    def __init__(self):
        self.message = "The provided subscription change is invalid"
        super().__init__(self.message)


class StartUpdateSubscription(BaseUseCase):
    def __init__(
        self, request_scope: RequestScope, stripe: StripeRepository | None = None
    ):
        super().__init__(request_scope)
        self.stripe = stripe or StripeRepository()

    def _store_raw_data(self, data: InvoicePaymentSucceeded) -> None:
        self.get_repository(Collection.BILLING_AUDIT_EVENTS).create(
            CreateAuditEvent(
                company_id=None,
                type="start_update_subscription",
                data=data.model_dump(),
            )
        )

    def validate_subscription_can_be_changed(
        self, company_subscription: CompanySubscription
    ):
        if company_subscription.plan == SubscriptionPlan.APPSUMO:
            raise CannotUpdateSubscriptionException(
                "Cannot update an AppSumo subscription"
            )
        if company_subscription.plan == SubscriptionPlan.GOLD_TRIAL:
            raise CannotUpdateSubscriptionException(
                "Cannot update a Gold Trial subscription, new subscription must be created"
            )
        if (
            company_subscription is None
            or company_subscription.stripe_subscription_id is None
        ):
            raise NoInitialSubscriptionException

    def start_update_subscription(
        self, company_id: str, new_plan: SubscriptionPlan
    ) -> CompanySubscription:
        """
        Usage is not changed by this process, they are still at the same limits/usability while the process is processed between the subscriptions
        """
        if new_plan in [SubscriptionPlan.APPSUMO, SubscriptionPlan.GOLD_TRIAL]:
            # Can not go from any existing subscription INTO appsomo or gold trial
            raise BadSubscriptionChange

        company_subscription_repo = CompanySubscriptionRepository(
            self.request_scope, company_id
        )
        company_subscription = company_subscription_repo.get_sub_entity()
        self.validate_subscription_can_be_changed(company_subscription)
        results = self.stripe.update_subscription(
            str(company_subscription.stripe_subscription_id),
            SUBSCRIPTION_PRICE_MAP[new_plan],
        )
        company_subscription.update_to_new_subscription(new_plan, results.id)
        return company_subscription_repo.set_sub_entity(company_subscription)
