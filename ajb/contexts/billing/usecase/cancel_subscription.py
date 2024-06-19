"""
This module handles cancelling a users subscription.
It will set the subscription status to cancelled and tell stripe to cancel the subscription.
"""

from datetime import datetime
from ajb.base import BaseUseCase, Collection, RequestScope
from ajb.contexts.companies.models import Company
from ajb.contexts.billing.subscriptions.models import (
    CompanySubscription,
)
from ajb.contexts.billing.subscriptions.repository import CompanySubscriptionRepository
from ajb.contexts.billing.subscriptions.models import (
    SubscriptionStatus,
    SubscriptionPlan,
)
from ajb.contexts.billing.billing_audit_events.models import CreateAuditEvent

from ajb.vendor.stripe.repository import StripeRepository


class NoSubscriptioToCancel(Exception):
    pass


class CancelSubscription(BaseUseCase):
    def __init__(
        self, request_scope: RequestScope, stripe: StripeRepository | None = None
    ):
        super().__init__(request_scope)
        self.stripe = stripe or StripeRepository()

    def _store_cancellation_data(self, data: dict) -> None:
        self.get_repository(Collection.BILLING_AUDIT_EVENTS).create(
            CreateAuditEvent(company_id=None, data=data, type="subscription_cancelled")
        )

    def _complete_cancellation(
        self,
        company: Company,
        company_subscription: CompanySubscription,
        reason: str | None,
        stripe_response: dict,
    ) -> CompanySubscription:
        subscription_repo = CompanySubscriptionRepository(
            self.request_scope, company.id
        )
        self._store_cancellation_data(
            {"company_id": company.id, "reason": reason, "stripe_data": stripe_response}
        )
        company_subscription.subscription_status = SubscriptionStatus.CANCELLED
        company_subscription.end_date = datetime.now()
        return subscription_repo.set_sub_entity(company_subscription)

    def cancel_company_subscription(
        self, company_id: str, reason: str | None
    ) -> CompanySubscription:
        company: Company = self.get_object(Collection.COMPANIES, company_id)
        subscription_repo = CompanySubscriptionRepository(
            self.request_scope, company.id
        )
        company_subscription = subscription_repo.get_sub_entity()
        if company_subscription.plan in [
            SubscriptionPlan.GOLD_TRIAL,
            SubscriptionPlan.APPSUMO,
        ]:
            return self._complete_cancellation(
                company, company_subscription, reason, {}
            )

        if company_subscription.stripe_subscription_id is None:
            raise NoSubscriptioToCancel
        stripe_response = self.stripe.cancel_subscription(
            company_subscription.stripe_subscription_id
        )
        return self._complete_cancellation(
            company, company_subscription, reason, stripe_response
        )
