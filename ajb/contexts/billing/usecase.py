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
    CreateInvoiceData,
    InvoiceLineItem,
    generate_invoice_number,
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

    def convert_usage_to_stripe_invoice_data(
        self, company: Company, subscription: CompanySubscription, usage: MonthlyUsage
    ) -> CreateInvoiceData | None:
        if not company.stripe_customer_id:
            raise ValueError("Company does not have a stripe customer id")
        invoice_data = CreateInvoiceData(
            stripe_customer_id=company.stripe_customer_id,
            description=f"Angie's Job Matcher Usage for {self._convert_billing_period_to_date_range(usage.billing_period)}",
            invoice_number=generate_invoice_number(company.id, usage.billing_period),
            invoice_items=[],
        )
        for usage_type, count in usage.transaction_counts.items():
            subscription_usage_details = subscription.usage_cost_details[usage_type]
            count_after_free_tier = max(
                0, count - subscription_usage_details.free_tier_limit_per_month
            )
            if count_after_free_tier == 0:
                continue
            invoice_data.invoice_items.append(
                InvoiceLineItem(
                    description=usage_type.value,
                    unit_amount_decimal=str(
                        subscription.usage_cost_details[
                            usage_type
                        ].cost_usd_per_transaction
                        * 100
                    ),
                    quantity=count,
                )
            )
        if len(invoice_data.invoice_items) == 0:
            return None
        return invoice_data

    def generate_stripe_invoice(
        self, company_id: str, billing_period: str | None = None
    ):
        company_with_stripe_id = (
            self._get_or_update_company_with_created_stripe_company_id(company_id)
        )
        subscription = self.get_or_create_company_subscription(company_id)
        usage = self.get_or_create_company_usage(company_id, billing_period)
        invoice_data = self.convert_usage_to_stripe_invoice_data(
            company_with_stripe_id, subscription, usage
        )
        if not invoice_data:
            return None
        return self.stripe.create_invoice(invoice_data)
