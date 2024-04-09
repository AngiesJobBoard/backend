from ajb.base import BaseUseCase, Collection, RepoFilterParams, Pagination
from ajb.contexts.billing.subscriptions.models import (
    CompanySubscription,
    CreateCompanySubscription,
    UserUpdateCompanySubscription,
)
from ajb.exceptions import EntityNotFound
from ajb.vendor.arango.models import Filter

from .usage.models import (
    CreateMonthlyUsage,
    MonthlyUsage,
    generate_billing_period_string,
)
from .billing_models import UsageType, SUBSCRIPTION_USAGE_COST_DETAIL_DEFAULTS


class CompanyBillingUsecase(BaseUseCase):
    def get_or_create_company_subscription(
        self, company_id: str
    ) -> CompanySubscription:
        subscription_repo = self.get_repository(
            Collection.COMPANY_SUBSCRIPTIONS, self.request_scope, company_id
        )
        try:
            return subscription_repo.get_one(company_id=company_id)
        except EntityNotFound:
            return subscription_repo.create(
                CreateCompanySubscription.get_default_subscription(company_id)
            )

    def update_company_subscription(
        self, company_id: str, data: UserUpdateCompanySubscription
    ):
        subscription_repo = self.get_repository(
            Collection.COMPANY_SUBSCRIPTIONS, self.request_scope, company_id
        )
        subscription = self.get_or_create_company_subscription(company_id)
        subscription.usage_cost_details = SUBSCRIPTION_USAGE_COST_DETAIL_DEFAULTS[
            data.plan
        ]
        subscription.plan = data.plan
        return subscription_repo.update(subscription.id, subscription)

    def _get_company_recruiter_count(self, company_id: str):
        recruiter_repo = self.get_repository(
            Collection.COMPANY_RECRUITERS, self.request_scope, company_id
        )
        return recruiter_repo.get_count(company_id=company_id)

    def get_or_create_company_current_usage(self, company_id: str) -> MonthlyUsage:
        usage_repo = self.get_repository(
            Collection.COMPANY_SUBSCRIPTION_USAGE_AND_BILLING,
            self.request_scope,
            company_id,
        )
        current_billing_period = generate_billing_period_string()

        try:
            return usage_repo.get_one(
                company_id=company_id, billing_period=current_billing_period
            )
        except EntityNotFound:
            return usage_repo.create(
                CreateMonthlyUsage.get_default_usage(
                    company_id, self._get_company_recruiter_count(company_id)
                )
            )

    def get_historic_company_usage(
        self, company_id: str, page: int = 0, page_size: int = 10
    ) -> tuple[list[MonthlyUsage], int]:
        usage_repo = usage_repo = self.get_repository(
            Collection.COMPANY_SUBSCRIPTION_USAGE_AND_BILLING,
            self.request_scope,
            company_id,
        )
        query = RepoFilterParams(
            pagination=Pagination(page=page, page_size=page_size),
            filters=[Filter(field="company_id", value=company_id)],
        )
        return usage_repo.query(repo_filters=query)

    def create_or_update_month_usage(
        self, company_id: str, usage: CreateMonthlyUsage
    ) -> MonthlyUsage:
        usage_repo = self.get_repository(
            Collection.COMPANY_SUBSCRIPTION_USAGE_AND_BILLING,
            self.request_scope,
            company_id,
        )
        subscription = self.get_or_create_company_subscription(company_id)
        current_usage = self.get_or_create_company_current_usage(company_id)
        current_usage.add_usage(usage, subscription.usage_cost_details)
        return usage_repo.update(current_usage.id, current_usage)

    def increment_company_usage(
        self, company_id: str, incremental_usages: dict[UsageType, int]
    ):
        return self.create_or_update_month_usage(
            company_id,
            CreateMonthlyUsage(
                company_id=company_id, transaction_counts=incremental_usages
            ),
        )
