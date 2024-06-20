"""
This is a module to check if an action is within the usage limits of a subscription plan
"""

from datetime import datetime
from cachetools import cached
from fastapi import HTTPException

from ajb.base import BaseUseCase, RequestScope
from ajb.contexts.billing.subscriptions.models import SubscriptionStatus
from ajb.contexts.billing.usecase.billing_usecase import (
    NoSubscriptionUsageAllottedException,
)
from ajb.exceptions import (
    TierLimitHitException,
    FeatureNotAvailableOnTier,
    EntityNotFound,
)

from .billing_models import UsageType, TierFeatures
from .usecase import CompanyBillingUsecase
from .subscription_cache import SUBSCRIPTION_CACHE


class SubscriptionValidationError(HTTPException):
    def __init__(self, message: str):
        super().__init__(status_code=402, detail=message)


class BillingValidateUsageUseCase(BaseUseCase):
    def __init__(
        self,
        request_scope: RequestScope,
        company_id: str,
        billing_usecase: CompanyBillingUsecase | None = None,
    ):
        self.request_scope = request_scope
        self.billing_usecase = billing_usecase or CompanyBillingUsecase(request_scope)
        self.subscription = self._get_company_subscription(company_id)
        self.usage = self._get_company_current_usage(company_id)

    @cached(SUBSCRIPTION_CACHE)
    def _get_company_subscription(self, company_id: str):
        # AJBTODO the subscription can be changed, this cache should appropriately handle that
        try:
            return self.billing_usecase.get_company_subscription(company_id)
        except EntityNotFound:
            raise SubscriptionValidationError("No subscription found for company")

    def _get_company_current_usage(self, company_id: str):
        """Will raise NoUsageAllottedtoCompanyException if no usage found"""
        try:
            return self.billing_usecase.get_current_company_usage(company_id)
        except NoSubscriptionUsageAllottedException:
            raise SubscriptionValidationError("No usage found for company")

    def validate_usage(
        self,
        company_id: str,
        usage_type: UsageType,
        amount_of_new_usage: int,
        increment_usage: bool = True,
    ) -> None:
        """
        Generally the amount of new usage is just 1.
        There is no handling if it is greater than 1 but could handle 1 more within the limit (for instance)
        This could be added later if needed.
        """
        # Check subscription is active
        if self.subscription.subscription_status not in [
            SubscriptionStatus.ACTIVE,
            SubscriptionStatus.PENDING_UPDATE_PAYMENT,
        ]:
            raise SubscriptionValidationError("Subscription is not active")

        # Check usage is not expired
        if self.usage.usage_expires and self.usage.usage_expires < datetime.now():
            raise SubscriptionValidationError("Usage has expired")

        # Check if usage has hit tier limit
        current_usage = self.usage.transaction_counts[usage_type]
        current_usage_limit = self.subscription.usage_cost_details[
            usage_type
        ].free_tier_limit_per_month

        if (
            current_usage_limit
            and current_usage + amount_of_new_usage > current_usage_limit
        ):
            raise TierLimitHitException

        # Allow action to continue and increment usage on subscription usage object
        if increment_usage:
            self.billing_usecase.increment_company_usage(
                company_id, usage_type, amount_of_new_usage
            )

    def validate_feature_access(self, feature: TierFeatures):
        if TierFeatures.ALL_FEATURES in self.subscription.subscription_features:
            return

        if feature not in self.subscription.subscription_features:
            raise SubscriptionValidationError(
                f"Feature {feature} is not available on this tier"
            )
