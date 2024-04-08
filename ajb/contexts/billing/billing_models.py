from enum import Enum
from pydantic import BaseModel


class SubscriptionPlan(str, Enum):
    """
    Starter is 0 per month then pay as you go
    Other plans progressively more expensive per month but marginally cheaper per action
    """

    STARTER = "Starter"
    SMALL_BUSINESS = "Small Business"
    MEDIUM_BUSINESS = "Medium Business"
    ENTERPRISE = "Enterprise"


class CompanyFreeTier(BaseModel):
    no_cost_resume_scans_per_month: int
    no_cost_match_scores_per_month: int
    no_cost_application_questions_answered_per_month: int
    no_cost_email_ingress_per_month: int
    no_cost_api_ingress_per_month: int
    no_cost_api_egress_per_month: int
    no_cost_total_recruiters_per_month: int


class CompanyRates(BaseModel):
    resume_scan_cost_usd_per_transaction: float
    match_score_cost_usd_per_transaction: float
    application_questions_answered_cost_usd_per_transaction: float
    email_ingress_cost_usd_per_transaction: float
    api_ingress_cost_usd_per_transaction: float
    api_egress_cost_usd_per_transaction: float
    total_recruiters_cost_usd_per_transaction: float


SUBSCRIPTION_FREE_TIERS: dict[SubscriptionPlan, CompanyFreeTier] = {
    SubscriptionPlan.STARTER: CompanyFreeTier(
        no_cost_resume_scans_per_month=50,
        no_cost_match_scores_per_month=50,
        no_cost_application_questions_answered_per_month=250,
        no_cost_email_ingress_per_month=50,
        no_cost_api_ingress_per_month=100,
        no_cost_api_egress_per_month=250,
        no_cost_total_recruiters_per_month=10,
    ),
    SubscriptionPlan.SMALL_BUSINESS: CompanyFreeTier(
        no_cost_resume_scans_per_month=1000,
        no_cost_match_scores_per_month=1000,
        no_cost_application_questions_answered_per_month=5000,
        no_cost_email_ingress_per_month=1000,
        no_cost_api_ingress_per_month=2000,
        no_cost_api_egress_per_month=5000,
        no_cost_total_recruiters_per_month=20,
    ),
    SubscriptionPlan.MEDIUM_BUSINESS: CompanyFreeTier(
        no_cost_resume_scans_per_month=5000,
        no_cost_match_scores_per_month=5000,
        no_cost_application_questions_answered_per_month=25000,
        no_cost_email_ingress_per_month=5000,
        no_cost_api_ingress_per_month=10000,
        no_cost_api_egress_per_month=25000,
        no_cost_total_recruiters_per_month=50,
    ),
    SubscriptionPlan.ENTERPRISE: CompanyFreeTier(
        no_cost_resume_scans_per_month=10000,
        no_cost_match_scores_per_month=10000,
        no_cost_application_questions_answered_per_month=50000,
        no_cost_email_ingress_per_month=10000,
        no_cost_api_ingress_per_month=20000,
        no_cost_api_egress_per_month=50000,
        no_cost_total_recruiters_per_month=100,
    ),
}

SUBSCRIPTION_RATES: dict[SubscriptionPlan, CompanyRates] = {
    SubscriptionPlan.STARTER: CompanyRates(
        resume_scan_cost_usd_per_transaction=1.0,
        match_score_cost_usd_per_transaction=1.0,
        application_questions_answered_cost_usd_per_transaction=1.0,
        email_ingress_cost_usd_per_transaction=1.0,
        api_ingress_cost_usd_per_transaction=1.0,
        api_egress_cost_usd_per_transaction=1.0,
        total_recruiters_cost_usd_per_transaction=1.0,
    ),
    SubscriptionPlan.SMALL_BUSINESS: CompanyRates(
        resume_scan_cost_usd_per_transaction=0.1,
        match_score_cost_usd_per_transaction=0.1,
        application_questions_answered_cost_usd_per_transaction=0.1,
        email_ingress_cost_usd_per_transaction=0.1,
        api_ingress_cost_usd_per_transaction=0.1,
        api_egress_cost_usd_per_transaction=0.1,
        total_recruiters_cost_usd_per_transaction=0.1,
    ),
    SubscriptionPlan.MEDIUM_BUSINESS: CompanyRates(
        resume_scan_cost_usd_per_transaction=0.05,
        match_score_cost_usd_per_transaction=0.05,
        application_questions_answered_cost_usd_per_transaction=0.05,
        email_ingress_cost_usd_per_transaction=0.05,
        api_ingress_cost_usd_per_transaction=0.05,
        api_egress_cost_usd_per_transaction=0.05,
        total_recruiters_cost_usd_per_transaction=0.05,
    ),
    SubscriptionPlan.ENTERPRISE: CompanyRates(
        resume_scan_cost_usd_per_transaction=0.01,
        match_score_cost_usd_per_transaction=0.01,
        application_questions_answered_cost_usd_per_transaction=0.01,
        email_ingress_cost_usd_per_transaction=0.01,
        api_ingress_cost_usd_per_transaction=0.01,
        api_egress_cost_usd_per_transaction=0.01,
        total_recruiters_cost_usd_per_transaction=0.01,
    ),
}
