from datetime import datetime
from pydantic import BaseModel

from ajb.base import BaseDataModel

from ..billing_models import CompanyRates, CompanyFreeTier


def generate_billing_period_string():
    now = datetime.now()
    return f"{now.year}-{now.month}"


class SystemCreateMonthlyUsage(BaseModel):
    company_id: str

    resume_scans: int = 0
    match_scores: int = 0
    application_questions_answered: int = 0
    email_ingress: int = 0
    api_ingress: int = 0
    api_egress: int = 0
    resume_storage: int = 0
    total_recruiters: int = 0

    outstanding_balance_usd: float = 0.0
    total_usage_usd: float = 0.0

    def calculate_total_usage_cost(
        self, free_tier: CompanyFreeTier, rates: CompanyRates
    ):
        total_cost = 0
        total_cost += (
            max([0, self.resume_scans - free_tier.no_cost_resume_scans_per_month])
            * rates.resume_scan_cost_usd_per_transaction
        )
        total_cost += (
            max([0, self.match_scores - free_tier.no_cost_match_scores_per_month])
            * rates.match_score_cost_usd_per_transaction
        )
        total_cost += (
            max(
                [
                    0,
                    self.application_questions_answered
                    - free_tier.no_cost_application_questions_answered_per_month,
                ]
            )
            * rates.application_questions_answered_cost_usd_per_transaction
        )
        total_cost += (
            max([0, self.email_ingress - free_tier.no_cost_email_ingress_per_month])
            * rates.email_ingress_cost_usd_per_transaction
        )
        total_cost += (
            max([0, self.api_ingress - free_tier.no_cost_api_ingress_per_month])
            * rates.api_ingress_cost_usd_per_transaction
        )
        total_cost += (
            max([0, self.api_egress - free_tier.no_cost_api_egress_per_month])
            * rates.api_egress_cost_usd_per_transaction
        )
        total_cost += (
            max(
                [
                    0,
                    self.total_recruiters
                    - free_tier.no_cost_total_recruiters_per_month,
                ]
            )
            * rates.total_recruiters_cost_usd_per_transaction
        )

        return total_cost


class CreateMonthlyUsage(SystemCreateMonthlyUsage):
    billing_period: str = generate_billing_period_string()


class MonthlyUsage(BaseDataModel, CreateMonthlyUsage):

    def add_usage(self, new_usage: CreateMonthlyUsage):
        self.resume_scans += new_usage.resume_scans
        self.match_scores += new_usage.match_scores
        self.application_questions_answered += new_usage.application_questions_answered
        self.email_ingress += new_usage.email_ingress
        self.api_ingress += new_usage.api_ingress
        self.api_egress += new_usage.api_egress
        self.resume_storage += new_usage.resume_storage
        self.total_recruiters += new_usage.total_recruiters
        self.total_usage_usd += new_usage.total_usage_usd
        return self
