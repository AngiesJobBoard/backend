"""
This is a module to check if an action is within the usage limits of a subscription plan
"""

from datetime import datetime
from cachetools import cached

from ajb.base import BaseUseCase, RequestScope
from ajb.contexts.billing.subscriptions.models import SubscriptionStatus
from ajb.exceptions import TierLimitHitException, FeatureNotAvailableOnTier

from .billing_models import UsageType, TierFeatures
from .usecase import CompanyBillingUsecase
from .subscription_cache import SUBSCRIPTION_CACHE


class SubscriptionNotActiveException(Exception):
    pass


class SubscriptionExpiredException(Exception):
    pass


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
        return self.billing_usecase.get_company_subscription(company_id)

    def _get_company_current_usage(self, company_id: str):
        """Will raise NoUsageAllottedtoCompanyException if no usage found"""
        return self.billing_usecase.get_current_company_usage(company_id)

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
        if self.subscription.subscription_status != SubscriptionStatus.ACTIVE:
            raise SubscriptionNotActiveException

        # Check usage is not expired
        if self.usage.usage_expires < datetime.now():
            raise SubscriptionExpiredException

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
            raise FeatureNotAvailableOnTier
