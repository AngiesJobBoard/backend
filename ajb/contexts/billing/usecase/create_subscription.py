"""
This module contains the business action for creating a new subscription
It also has the logic for any existing companies that have no subscription from before this was available
"""

from datetime import datetime

from ajb.base import BaseUseCase, Collection, RepoFilterParams, Pagination, RequestScope
from ajb.contexts.companies.models import Company
from ajb.contexts.billing.subscriptions.models import (
    CompanySubscription,
    CreateCompanySubscription,
    UserUpdateCompanySubscription,
)
from ajb.vendor.stripe.repository import StripeRepository

from ..billing_models import SubscriptionPlan


class CreateSubscription(BaseUseCase):
    def __init__(
        self, request_scope: RequestScope, stripe: StripeRepository | None = None
    ):
        super().__init__(request_scope)
        self.stripe = stripe or StripeRepository()
    
    def create_subscription_link(self, company_id: str):
        # Create company in stripe and update company object

        # User will click link to fill out payment details and stuff

        # stripe then posts the data w/ confirmation back to us and we create subscription
        ...
    
    def create_subscription(
        self, company_id: str, plan: SubscriptionPlan
    ) -> CompanySubscription:
        ...
