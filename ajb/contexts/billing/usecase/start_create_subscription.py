"""
This module contains the business action for starting to create a new subscription
"""

from datetime import datetime, timedelta

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
from ajb.contexts.billing.usage.models import CreateMonthlyUsage, MonthlyUsage
from ajb.contexts.billing.usage.repository import CompanySubscriptionUsageRepository
from ajb.vendor.stripe.models import StripeCheckoutSessionCreated
from ajb.exceptions import EntityNotFound

from .SUBSCRIPTION_PRICE_MAP import SUBSCRIPTION_PRICE_MAP
from ..billing_models import SubscriptionPlan


class CompanyAlreadyHasSubscription(Exception):
    pass


class BadFirstSubscriptionPlan(Exception):
    def __init__(self):
        self.message = "The provided subscription is invalid, free trial or appsumo can only create standard subscriptions.s"
        super().__init__(self.message)


class BadAppSumoCode(Exception):
    def __init__(self):
        self.message = "The provided appsumo code is invalid."
        super().__init__(self.message)


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

    def check_if_company_already_has_subscription(
        self, company_id: str, plan_to_create: SubscriptionPlan
    ):
        """
        You can create a new subscription if you don't have one already OR if you plan is appsumo or gold trial.
        If you are on a trial you can not transfer to another trial or app sumo
        If you are on app sumo you can not transfer to another trial or app sumo
        """
        try:
            potential_subscription = CompanySubscriptionRepository(
                self.request_scope, company_id
            ).get_sub_entity()

            # If you on a trial, you can go to app sumo deal or a real plan
            if (
                potential_subscription.plan == SubscriptionPlan.GOLD_TRIAL
                and plan_to_create == SubscriptionPlan.GOLD_TRIAL
            ):
                raise BadFirstSubscriptionPlan

            # If you're an app sumo, you can only go up to a real plan
            if (
                potential_subscription.plan == SubscriptionPlan.APPSUMO
                and plan_to_create
                in [
                    SubscriptionPlan.GOLD_TRIAL,
                    SubscriptionPlan.APPSUMO,
                ]
            ):
                raise BadFirstSubscriptionPlan

            if potential_subscription.plan in [
                SubscriptionPlan.GOLD_TRIAL,
                SubscriptionPlan.APPSUMO,
            ]:
                return

            # If you're on a real plan, you can not create an additional subscription it has to be updated
            raise CompanyAlreadyHasSubscription

        except EntityNotFound:
            return

    def start_create_subscription(
        self, company_id: str, plan: SubscriptionPlan, appsumo_code: str | None
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
        self.check_if_company_already_has_subscription(company_id, plan)

        if plan == SubscriptionPlan.GOLD_TRIAL:
            return self.create_free_trial_subscription(company)
        if plan == SubscriptionPlan.APPSUMO:
            if not appsumo_code:
                raise BadAppSumoCode
            return self.create_appsumo_subscription(company, appsumo_code)

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
            CreateCompanySubscription.create_subscription(
                company.id,
                str(company.stripe_customer_id),
                plan,
                checkout_session,
            )
        )

    def create_free_trial_subscription(self, company: Company) -> CompanySubscription:
        """
        The user has an option to elect for a free trial. This will no require them to go
        to stripe or pay for anything. It will create an active free trial subscription object.
        This will expire in 2 weeks and become a pending first payment status.
        """
        created_usage = CompanySubscriptionUsageRepository(
            self.request_scope, company.id
        ).create(
            CreateMonthlyUsage(
                company_id=company.id,
                usage_expires=datetime.now()
                + timedelta(days=14),  # 14 days of free gold
                invoice_details=None,
                free_trial_usage=True,
            )
        )
        created_subscription = CompanySubscriptionRepository(
            self.request_scope, company.id
        ).set_sub_entity(
            CreateCompanySubscription.create_trial_subscription(
                company.id, created_usage.id
            )
        )
        return created_subscription

    def _validate_appsumo_code(self, appsumo_code: str) -> bool:
        # Where are codes stored? How are they generated? How are they validated?
        ...

    def create_appsumo_subscription(
        self, company: Company, appsumo_code: str
    ) -> CompanySubscription:
        """
        The user has an option to elect for an appsumo subscription. This will no require them to go
        to stripe or pay for anything. Their subscription will be validated from a code they've provided.
        If the code is correct the usage will not expire and the subscription will become active immediately.
        """
        self._validate_appsumo_code(appsumo_code)  # Will throw an exception if invalid
        created_usage = CompanySubscriptionUsageRepository(
            self.request_scope, company.id
        ).create(
            CreateMonthlyUsage(
                company_id=company.id,
                usage_expires=None,
                invoice_details=None,
                free_trial_usage=False,
            )
        )
        created_subscription = CompanySubscriptionRepository(
            self.request_scope, company.id
        ).set_sub_entity(
            CreateCompanySubscription.create_app_sumo_subscription(
                company.id, created_usage.id
            )
        )
        return created_subscription
