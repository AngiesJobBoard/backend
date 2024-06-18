"""
This is a module to check if an action is within the usage limits of a subscription plan
"""

from datetime import datetime
from cachetools import cached

from ajb.base import BaseUseCase, RequestScope, Collection, RepoFilterParams
from ajb.contexts.applications.models import ScanStatus
from ajb.vendor.arango.models import Filter, Operator
from ajb.exceptions import TierLimitHitException, FeatureNotAvailableOnTier

from .billing_models import UsageType, TierFeatures
from .usecase import CompanyBillingUsecase
from .subscription_cache import SUBSCRIPTION_CACHE


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
        usage_detail = self.subscription.usage_cost_details[usage_type]
        if usage_detail.unlimited_use:
            # Do not block unlimited use
            return

        if (
            self.subscription.gold_trial_expires
            and datetime.now() < self.subscription.gold_trial_expires
        ):
            # Do not block usage during pro trial
            return

        if usage_detail.blocked_after_free_tier is False:
            # Allow usage to increment - incurs charge per use and doesn't matter what usage is
            return

        current_usage = self.usage.transaction_counts[usage_type]
        if current_usage + amount_of_new_usage > usage_detail.free_tier_limit_per_month:
            # Block usage if free tier limit hit
            raise TierLimitHitException

        # Allow action to continue and increment usage on subscription usage object
        if increment_usage:
            self.billing_usecase.increment_company_usage(
                company_id, usage_type, amount_of_new_usage
            )

    def validate_feature_access(self, feature: TierFeatures):
        if feature not in self.subscription.subscription_features:
            raise FeatureNotAvailableOnTier
