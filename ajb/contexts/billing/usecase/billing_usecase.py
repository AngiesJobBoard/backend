from datetime import datetime

from ajb.base import BaseUseCase, Collection, RepoFilterParams, Pagination, RequestScope
from ajb.contexts.companies.models import Company
from ajb.contexts.billing.subscriptions.models import (
    CompanySubscription,
    CreateCompanySubscription,
    UserUpdateCompanySubscription,
)
from ajb.exceptions import EntityNotFound
from ajb.vendor.arango.models import Filter
from ajb.vendor.stripe.repository import (
    StripeRepository,
)

from ajb.contexts.billing.usage.models import (
    CreateMonthlyUsage,
    MonthlyUsage,
    generate_billing_period_string,
)
from ajb.contexts.billing.billing_models import (
    UsageType,
    SUBSCRIPTION_USAGE_COST_DETAIL_DEFAULTS,
)
from ..subscription_cache import SUBSCRIPTION_CACHE


class NoLineItemsToInvoiceException(Exception):
    pass


class StripeCustomerIDMissingException(Exception):
    pass


class CompanyBillingUsecase(BaseUseCase):
    def __init__(
        self, request_scope: RequestScope, stripe: StripeRepository | None = None
    ):
        super().__init__(request_scope)
        self.stripe = stripe or StripeRepository()

    def get_or_create_company_subscription(
        self, company_id: str
    ) -> CompanySubscription:
        subscription_repo = self.get_repository(
            Collection.COMPANY_SUBSCRIPTIONS, self.request_scope, company_id
        )
        return subscription_repo.get_one(company_id=company_id)

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
        results = subscription_repo.update(subscription.id, subscription)
        SUBSCRIPTION_CACHE[company_id] = results
        return results

    def _get_company_recruiter_count(self, company_id: str):
        recruiter_repo = self.get_repository(
            Collection.COMPANY_RECRUITERS, self.request_scope, company_id
        )
        return recruiter_repo.get_count(company_id=company_id)

    def get_or_create_company_usage(
        self, company_id: str, billing_period: str | None = None
    ) -> MonthlyUsage:
        """Default usage is current if not provided."""
        usage_repo = self.get_repository(
            Collection.COMPANY_SUBSCRIPTION_USAGE_AND_BILLING,
            self.request_scope,
            company_id,
        )
        billing_period = billing_period or generate_billing_period_string()

        try:
            return usage_repo.get_one(
                company_id=company_id, billing_period=billing_period
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
        current_usage = self.get_or_create_company_usage(company_id)
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
    
    def set_company_usage(
        self, company_id: str, usages_to_set: dict[UsageType, int]
    ):
        usage_repo = self.get_repository(
            Collection.COMPANY_SUBSCRIPTION_USAGE_AND_BILLING,
            self.request_scope,
            company_id,
        )
        current_usage = self.get_or_create_company_usage(company_id)
        current_usage.transaction_counts.update(usages_to_set)
        return usage_repo.update(current_usage.id, current_usage)

    def _get_company_name_with_id(self, company: Company):
        return f"{company.name} - {company.id}"

    def _get_or_update_company_with_created_stripe_company_id(
        self, company_id: str
    ) -> Company:
        company_repo = self.get_repository(Collection.COMPANIES, self.request_scope)
        company: Company = company_repo.get(company_id)
        if company.stripe_customer_id is not None:
            return company

        new_stripe_customer = self.stripe.create_customer(
            self._get_company_name_with_id(company), company.owner_email, company.id
        )
        return company_repo.update_fields(
            company.id, stripe_customer_id=new_stripe_customer.id
        )

    def _convert_billing_period_to_date_range(self, billing_period: str):
        period_as_dt = datetime.strptime(billing_period, "%Y-%m")
        return period_as_dt.strftime("%B %Y")
