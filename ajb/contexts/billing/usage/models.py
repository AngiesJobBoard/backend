from datetime import datetime
from pydantic import BaseModel

from ajb.base import BaseDataModel

from ..billing_models import UsageType, UsageDetail


def generate_billing_period_string():
    now = datetime.now()
    return f"{now.year}-{now.month}"


class BillingAfterBlockedFreeTierError(Exception):
    pass


class CreateMonthlyUsage(BaseModel):
    company_id: str
    billing_period: str = generate_billing_period_string()

    transaction_counts: dict[UsageType, int] = {
        UsageType.APPLICATIONS_PROCESSED: 0,
        UsageType.TOTAL_JOBS: 0,
        UsageType.TOTAL_RECRUITERS: 0,
    }

    outstanding_balance_usd: float = 0.0
    total_usage_usd: float = 0.0
    stripe_invoice_id: str | None = None

    def calculate_total_usage_cost(
        self, usage_cost_details: dict[UsageType, UsageDetail]
    ):
        total_cost = 0.0
        for usage_type, usage_count in self.transaction_counts.items():
            usage_detail = usage_cost_details[usage_type]
            if usage_detail.unlimited_use:
                continue
            if usage_count > usage_detail.free_tier_limit_per_month:
                if usage_detail.blocked_after_free_tier:
                    raise BillingAfterBlockedFreeTierError
                total_cost += (
                    float(usage_count - usage_detail.free_tier_limit_per_month)
                    * usage_detail.cost_usd_per_transaction
                )
        self.total_usage_usd = total_cost

    @classmethod
    def get_default_usage(
        cls, company_id: str, num_recruiters: int
    ) -> "CreateMonthlyUsage":
        return cls(
            company_id=company_id,
            transaction_counts={
                UsageType.APPLICATIONS_PROCESSED: 0,
                UsageType.TOTAL_JOBS: 0,
                UsageType.TOTAL_RECRUITERS: num_recruiters,
            },
        )


class MonthlyUsage(BaseDataModel, CreateMonthlyUsage):

    def add_usage(
        self,
        usage: CreateMonthlyUsage,
        usage_cost_details: dict[UsageType, UsageDetail],
    ):
        for usage_type, usage_count in usage.transaction_counts.items():
            self.transaction_counts[usage_type] += usage_count

        self.calculate_total_usage_cost(usage_cost_details)
