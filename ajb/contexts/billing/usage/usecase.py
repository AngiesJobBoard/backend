from ajb.base import BaseUseCase, Collection
from ajb.contexts.billing.subscriptions.models import CompanySubscription
from ajb.exceptions import EntityNotFound

from .models import CreateMonthlyUsage, MonthlyUsage


class CompanySubscriptionUsageUsecase(BaseUseCase):
    def create_or_update_month_usage(
        self, company_id: str, usage: CreateMonthlyUsage
    ) -> MonthlyUsage:
        subscription_repo = self.get_repository(
            Collection.COMPANY_SUBSCRIPTIONS, self.request_scope, company_id
        )
        usage_repo = self.get_repository(
            Collection.COMPANY_SUBSCRIPTION_USAGE_AND_BILLING,
            self.request_scope,
            company_id,
        )
        subscription: CompanySubscription = subscription_repo.get_one(
            company_id=company_id
        )
        usage.total_usage_usd = usage.calculate_total_usage_cost(
            subscription.free_tier, subscription.rates
        )

        # If usage exists, add values to existing usage
        try:
            potential_current_usage: MonthlyUsage = usage_repo.get_one(
                company_id=company_id, billing_period=usage.billing_period
            )
            potential_current_usage.add_usage(usage)
            return usage_repo.update(
                potential_current_usage.id, potential_current_usage
            )
        except EntityNotFound:
            # Create new usage for this month
            return usage_repo.create(usage)
