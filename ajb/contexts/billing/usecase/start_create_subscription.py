"""
This module contains the business action for starting to create a new subscription
"""

import os

from ajb.base import BaseUseCase, Collection, RequestScope
from ajb.contexts.companies.models import Company
from ajb.contexts.billing.subscriptions.models import (
    CompanySubscription,
    CreateCompanySubscription,
    SubscriptionStatus,
)
from ajb.contexts.billing.subscriptions.repository import CompanySubscriptionRepository
from ajb.vendor.stripe.repository import StripeRepository
from ajb.contexts.billing.billing_audit_events.models import CreateAuditEvent
from ajb.vendor.stripe.models import StripeCheckoutSessionCreated
from ajb.exceptions import EntityNotFound

from ..billing_models import SubscriptionPlan

# Not sure the best way to reference this data... so for now it's hardcoded? Replaceable by env vars? Who knows
APP_SUMO_PRICE_ID = os.getenv("APP_SUMO_PRICE_ID", "price_1PSmTMDd0dqh9J6nKDa2buRV")
SILVER_TIER_PRICE_ID = os.getenv(
    "SILVER_TIER_PRICE_ID", "price_1PSmOVDd0dqh9J6nPqTZWjG5"
)
GOLD_TIER_PRICE_ID = os.getenv("GOLD_TIER_PRICE_ID", "price_1PSmOwDd0dqh9J6nisDSnpYZ")
PLATINUM_TIER_PRICE_ID = os.getenv(
    "PLATINUM_TIER_PRICE_ID", "price_1PSmPHDd0dqh9J6nF16RWPbC"
)


SUBSCRIPTION_PRICE_MAP: dict[SubscriptionPlan, str] = {
    SubscriptionPlan.APPSUMO: APP_SUMO_PRICE_ID,
    SubscriptionPlan.SILVER: SILVER_TIER_PRICE_ID,
    SubscriptionPlan.GOLD: GOLD_TIER_PRICE_ID,
    SubscriptionPlan.PLATINUM: PLATINUM_TIER_PRICE_ID,
}


class CompanyAlreadyHasSubscription(Exception):
    pass


class StartCreateSubscription(BaseUseCase):
    def __init__(
        self, request_scope: RequestScope, stripe: StripeRepository | None = None
    ):
        super().__init__(request_scope)
        self.stripe = stripe or StripeRepository()

    def _store_raw_checkout_session_data(
        self, data: StripeCheckoutSessionCreated
    ) -> None:
        self.get_repository(Collection.BILLING_AUDIT_EVENTS).create(
            CreateAuditEvent(
                company_id=None,
                type="stripe_checkout_session_created",
                data=data.model_dump(),
            )
        )

    def update_company_to_have_stripe_customer_id(self, company: Company) -> Company:
        results = self.stripe.create_customer(
            company.name, company.owner_email, company.id
        )
        return self.get_repository(Collection.COMPANIES).update_fields(
            company.id, stripe_customer_id=results.id
        )

    def _create_subscription_object(
        self,
        company: Company,
        plan: SubscriptionPlan,
        checkout_session: StripeCheckoutSessionCreated,
    ) -> CreateCompanySubscription:
        if plan == SubscriptionPlan.APPSUMO:
            return CreateCompanySubscription.create_app_sumo_subscription(
                company.id, str(company.stripe_customer_id), checkout_session
            )
        return CreateCompanySubscription.create_subscription(
            company.id,
            str(company.stripe_customer_id),
            plan,
            checkout_session,
        )

    def check_if_company_already_has_subscription(self, company_id: str):
        try:
            potential_subscription = CompanySubscriptionRepository(
                self.request_scope, company_id
            ).get_sub_entity()

            # Are there other statuses we want to handle??
            if potential_subscription.subscription_status in [
                SubscriptionStatus.ACTIVE,
            ]:
                raise CompanyAlreadyHasSubscription
        except EntityNotFound:
            return

    def start_create_subscription(
        self, company_id: str, plan: SubscriptionPlan
    ) -> CompanySubscription:
        """
        This starts the subscription process by making sure the company is registered in stripe
        and it will create their checkout page for them to pay for their subscription.

        Additionally, it will start and store the subscription object BUT it will not be active.

        After the user completes their payment in stripe there will be a POST request from stripe
        back to us with this confirmation. This will be handled in the CompleteSubscriptionUseCase
        and will finally activate the subscription for this company.
        """
        company: Company = self.get_object(Collection.COMPANIES, company_id)

        # Ensure the company is established in stripe as a customer
        if company.stripe_customer_id is None:
            company_with_stripe = self.update_company_to_have_stripe_customer_id(
                company
            )
        else:
            company_with_stripe = company

        # Create the session in stripe to get URL and things
        assert company_with_stripe.stripe_customer_id is not None
        if plan == SubscriptionPlan.APPSUMO:
            recurring = False
        else:
            recurring = True
        checkout_session = self.stripe.create_subscription_checkout_session(
            company_id,
            company_with_stripe.stripe_customer_id,
            SUBSCRIPTION_PRICE_MAP[plan],
            recurring,
        )

        # Store checkout for audit purposes
        self._store_raw_checkout_session_data(checkout_session)

        # Now create the company subscription object
        return CompanySubscriptionRepository(
            self.request_scope, company_id
        ).set_sub_entity(
            self._create_subscription_object(
                company_with_stripe, plan, checkout_session
            )
        )

    def create_free_trial_subscription(self, company_id: str) -> CompanySubscription:
        """
        The user has an option to elect for a free trial. This will no require them to go
        to stripe or pay for anything. It will create an active free trial subscription object.
        This will expire in 2 weeks and become a pending first payment status.
        """
        return self.get_repository(Collection.COMPANY_SUBSCRIPTIONS).create(
            CreateCompanySubscription.create_trial_subscription(company_id)
        )
