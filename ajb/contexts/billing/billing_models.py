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


class UsageType(str, Enum):
    RESUME_SCANS = "resume_scans"
    MATCH_SCORES = "match_scores"
    APPLICATION_QUESTIONS_ANSWERED = "application_questions_answered"
    EMAIL_INGRESS = "email_ingress"
    API_INGRESS = "api_ingress"
    API_EGRESS = "api_egress"
    TOTAL_RECRUITERS = "total_recruiters"


class UsageDetail(BaseModel):
    free_tier_limit_per_month: int = 0
    cost_usd_per_transaction: float


SUBSCRIPTION_USAGE_COST_DETAIL_DEFAULTS: dict[SubscriptionPlan, dict[UsageType, UsageDetail]] = {
    SubscriptionPlan.STARTER: {
        UsageType.RESUME_SCANS: UsageDetail(
            free_tier_limit_per_month=50, cost_usd_per_transaction=1.0
        ),
        UsageType.MATCH_SCORES: UsageDetail(
            free_tier_limit_per_month=50, cost_usd_per_transaction=1.0
        ),
        UsageType.APPLICATION_QUESTIONS_ANSWERED: UsageDetail(
            free_tier_limit_per_month=250, cost_usd_per_transaction=1.0
        ),
        UsageType.EMAIL_INGRESS: UsageDetail(
            free_tier_limit_per_month=50, cost_usd_per_transaction=1.0
        ),
        UsageType.API_INGRESS: UsageDetail(
            free_tier_limit_per_month=100, cost_usd_per_transaction=1.0
        ),
        UsageType.API_EGRESS: UsageDetail(
            free_tier_limit_per_month=250, cost_usd_per_transaction=1.0
        ),
        UsageType.TOTAL_RECRUITERS: UsageDetail(
            free_tier_limit_per_month=10, cost_usd_per_transaction=1.0
        ),
    },
    SubscriptionPlan.SMALL_BUSINESS: {
        UsageType.RESUME_SCANS: UsageDetail(
            free_tier_limit_per_month=1000, cost_usd_per_transaction=0.1
        ),
        UsageType.MATCH_SCORES: UsageDetail(
            free_tier_limit_per_month=1000, cost_usd_per_transaction=0.1
        ),
        UsageType.APPLICATION_QUESTIONS_ANSWERED: UsageDetail(
            free_tier_limit_per_month=5000, cost_usd_per_transaction=0.1
        ),
        UsageType.EMAIL_INGRESS: UsageDetail(
            free_tier_limit_per_month=1000, cost_usd_per_transaction=0.1
        ),
        UsageType.API_INGRESS: UsageDetail(
            free_tier_limit_per_month=2000, cost_usd_per_transaction=0.1
        ),
        UsageType.API_EGRESS: UsageDetail(
            free_tier_limit_per_month=5000, cost_usd_per_transaction=0.1
        ),
        UsageType.TOTAL_RECRUITERS: UsageDetail(
            free_tier_limit_per_month=20, cost_usd_per_transaction=0.1
        ),
    },
    SubscriptionPlan.MEDIUM_BUSINESS: {
        UsageType.RESUME_SCANS: UsageDetail(
            free_tier_limit_per_month=5000, cost_usd_per_transaction=0.05
        ),
        UsageType.MATCH_SCORES: UsageDetail(
            free_tier_limit_per_month=5000, cost_usd_per_transaction=0.05
        ),
        UsageType.APPLICATION_QUESTIONS_ANSWERED: UsageDetail(
            free_tier_limit_per_month=25000, cost_usd_per_transaction=0.05
        ),
        UsageType.EMAIL_INGRESS: UsageDetail(
            free_tier_limit_per_month=5000, cost_usd_per_transaction=0.05
        ),
        UsageType.API_INGRESS: UsageDetail(
            free_tier_limit_per_month=10000, cost_usd_per_transaction=0.05
        ),
        UsageType.API_EGRESS: UsageDetail(
            free_tier_limit_per_month=25000, cost_usd_per_transaction=0.05
        ),
        UsageType.TOTAL_RECRUITERS: UsageDetail(
            free_tier_limit_per_month=50, cost_usd_per_transaction=0.05
        ),
    },
    SubscriptionPlan.ENTERPRISE: {
        UsageType.RESUME_SCANS: UsageDetail(
            free_tier_limit_per_month=10000, cost_usd_per_transaction=0.01
        ),
        UsageType.MATCH_SCORES: UsageDetail(
            free_tier_limit_per_month=10000, cost_usd_per_transaction=0.01
        ),
        UsageType.APPLICATION_QUESTIONS_ANSWERED: UsageDetail(
            free_tier_limit_per_month=50000, cost_usd_per_transaction=0.01
        ),
        UsageType.EMAIL_INGRESS: UsageDetail(
            free_tier_limit_per_month=10000, cost_usd_per_transaction=0.01
        ),
        UsageType.API_INGRESS: UsageDetail(
            free_tier_limit_per_month=20000, cost_usd_per_transaction=0.01
        ),
        UsageType.API_EGRESS: UsageDetail(
            free_tier_limit_per_month=50000, cost_usd_per_transaction=0.01
        ),
        UsageType.TOTAL_RECRUITERS: UsageDetail(
            free_tier_limit_per_month=100, cost_usd_per_transaction=0.01
        ),
    },
}
