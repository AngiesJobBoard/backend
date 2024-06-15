"""
This is a module to check if an action is within the usage limits of a subscription plan
"""

from datetime import datetime
from cachetools import TTLCache, cached

from ajb.base import BaseUseCase, RequestScope, Collection, RepoFilterParams
from ajb.vendor.arango.models import Filter, Operator
from ajb.exceptions import TierLimitHitException, FeatureNotAvailableOnTier

from .billing_models import UsageType, TierFeatures
from .usecase import CompanyBillingUsecase


SUBSCRIPTION_CACHE = TTLCache(maxsize=100, ttl=60 * 5)


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

    @cached(SUBSCRIPTION_CACHE)
    def _get_company_subscription(self, company_id: str):
        return self.billing_usecase.get_or_create_company_subscription(company_id)

    def _get_recruiters_count(self, company_id: str):
        recruiter_repo = self.get_repository(
            Collection.COMPANY_RECRUITERS, self.request_scope, company_id
        )
        return recruiter_repo.get_count(company_id=company_id)

    def _get_total_jobs(self, company_id: str):
        job_repo = self.get_repository(Collection.JOBS, self.request_scope, company_id)
        return job_repo.get_count(company_id=company_id)

    def _get_total_applications_processed(self, company_id: str):
        """Only processed this month so far..."""
        application_repo = self.get_repository(Collection.APPLICATIONS)
        filter_params = RepoFilterParams(
            filters=[
                Filter(
                    field="created_at",
                    operator=Operator.GREATER_THAN_EQUAL,
                    value=datetime.now().replace(day=1, hour=0, minute=0, second=0),
                )
            ]
        )
        return application_repo.get_count(
            repo_filters=filter_params, company_id=company_id
        )

    def _get_usage_count(self, company_id: str, usage_type: UsageType):
        usage_fetch_funcs = {
            UsageType.APPLICATIONS_PROCESSED: self._get_total_applications_processed,
            UsageType.TOTAL_JOBS: self._get_total_jobs,
            UsageType.TOTAL_RECRUITERS: self._get_recruiters_count,
        }
        return usage_fetch_funcs[usage_type](company_id)

    def validate_usage(self, company_id: str, usage_type: UsageType) -> None:
        usage_detail = self.subscription.usage_cost_details[usage_type]
        if usage_detail.unlimited_use:
            # Do not block unlimited use
            return

        if (
            self.subscription.pro_trial_expires
            and datetime.now() < self.subscription.pro_trial_expires
        ):
            # Do not block usage during pro trial
            return

        if not usage_detail.blocked_after_free_tier:
            # Allow usage to increment - incurs charge per use and doesn't matter what usage is
            return

        current_usage = self._get_usage_count(company_id, usage_type)
        if current_usage >= usage_detail.free_tier_limit_per_month:
            # Block usage if free tier limit hit
            raise TierLimitHitException

    def validate_feature_access(self, feature: TierFeatures):
        if feature not in self.subscription.subscription_features:
            raise FeatureNotAvailableOnTier
