"""
This migration is only meant to be run once as we transition from an early beta into a paid product.
"""

from datetime import datetime

from ajb.base import BaseUseCase, Collection
from ajb.contexts.billing.billing_models import (
    SubscriptionPlan,
    TierFeatures,
    UsageDetail,
    UsageType,
)
from ajb.contexts.billing.subscriptions.models import (
    CreateCompanySubscription,
    SubscriptionStatus,
)
from ajb.contexts.billing.usage.models import CreateMonthlyUsage
from ajb.contexts.companies.models import Company

from migrations.base import MIGRATION_REQUEST_SCOPE


class AllCompaniesGetUnlimitedSubscriptionsMigration(BaseUseCase):
    """
    This migration is only meant to be run once as we transition from an early beta into a paid product.
    """

    def get_all_companies(self) -> list[Company]:
        company_repo = self.get_repository(Collection.COMPANIES)
        return company_repo.get_all()

    def update_company_subscription(self, company_id: str):
        # Create an active subscription with never ending unlimited usage (and all features)
        subscription_repo = self.get_repository(
            Collection.COMPANY_SUBSCRIPTIONS, self.request_scope, company_id
        )
        new_subscription = subscription_repo.set_sub_entity(
            CreateCompanySubscription(
                company_id=company_id,
                plan=SubscriptionPlan.PLATINUM,
                start_date=datetime.now(),
                checkout_session=None,
                subscription_features=[TierFeatures.ALL_FEATURES],
                subscription_status=SubscriptionStatus.ACTIVE,
                usage_cost_details={
                    UsageType.APPLICATIONS_PROCESSED: UsageDetail(
                        free_tier_limit_per_month=None,
                        blocked_after_free_tier=False,
                        unlimited_use=True,
                    ),
                    UsageType.TOTAL_JOBS: UsageDetail(
                        free_tier_limit_per_month=None,
                        blocked_after_free_tier=False,
                        unlimited_use=True,
                    ),
                    UsageType.TOTAL_RECRUITERS: UsageDetail(
                        free_tier_limit_per_month=None,
                        blocked_after_free_tier=False,
                        unlimited_use=True,
                    ),
                },
            )
        )
        new_usage = self.get_repository(
            Collection.COMPANY_SUBSCRIPTION_USAGE_AND_BILLING
        ).create(
            CreateMonthlyUsage(
                company_id=company_id, usage_expires=None, invoice_details=None
            )
        )
        subscription_repo.update_fields(
            new_subscription.id,
            current_usage_id=new_usage.id,
        )

    def run(self):
        companies = self.get_all_companies()
        for company in companies:
            print(f"Creating unlimited subscription for company {company.name}")
            self.update_company_subscription(company.id)


if __name__ == "__main__":
    AllCompaniesGetUnlimitedSubscriptionsMigration(MIGRATION_REQUEST_SCOPE).run()
