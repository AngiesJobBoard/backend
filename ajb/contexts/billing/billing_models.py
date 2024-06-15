from enum import Enum
from pydantic import BaseModel


class SubscriptionPlan(str, Enum):
    """
    Starter is 0 per month then pay as you go
    Other plans progressively more expensive per month but marginally cheaper per action
    """

    STARTER = "Starter"
    PRO = "Pro"
    ENTERPRISE = "Enterprise"


class UsageType(str, Enum):
    APPLICATIONS_PROCESSED = "applications_processed"
    TOTAL_JOBS = "total_jobs"
    TOTAL_RECRUITERS = "total_recruiters"


class UsageDetail(BaseModel):
    free_tier_limit_per_month: int = 0
    cost_usd_per_transaction: float = 0.0
    blocked_after_free_tier: bool = False
    unlimited_use: bool = False



class TierFeatures(str, Enum):
    PUBLIC_APPLICATION_PAGE = "public_application_page"
    EMAIL_INGRESS = "email_ingress"
    GENERATE_JOB_SKILLS = "generate_job_skills"
    GENERATE_JOB_QUESTIONS = "generate_job_questions"


SUBSCRIPTION_USAGE_COST_DETAIL_DEFAULTS: dict[
    SubscriptionPlan, dict[UsageType, UsageDetail]
] = {
    # 50 free applications per month then blocked. 5 jobs, only 1 recruiter - all blocked after free tier
    SubscriptionPlan.STARTER: {
        UsageType.APPLICATIONS_PROCESSED: UsageDetail(
            free_tier_limit_per_month=50, cost_usd_per_transaction=1.0, blocked_after_free_tier=True
        ),
        UsageType.TOTAL_JOBS: UsageDetail(
            free_tier_limit_per_month=5, cost_usd_per_transaction=1.0, blocked_after_free_tier=True
        ),
        UsageType.TOTAL_RECRUITERS: UsageDetail(
            free_tier_limit_per_month=1, cost_usd_per_transaction=1.0, blocked_after_free_tier=True
        ),
    },

    # 1000 free applications per month then 0.1 per application. 10 recruiters then 5 per recruiter per month, unlimited jobs
    SubscriptionPlan.PRO: {
        UsageType.APPLICATIONS_PROCESSED: UsageDetail(
            free_tier_limit_per_month=1000, cost_usd_per_transaction=0.1
        ),
        UsageType.TOTAL_JOBS: UsageDetail(
            unlimited_use=True
        ),
        UsageType.TOTAL_RECRUITERS: UsageDetail(
            free_tier_limit_per_month=10, cost_usd_per_transaction=5.0
        ),
    },

    # No limit plan
    SubscriptionPlan.ENTERPRISE: {
        UsageType.APPLICATIONS_PROCESSED: UsageDetail(
            unlimited_use=True
        ),
        UsageType.TOTAL_JOBS: UsageDetail(
            unlimited_use=True
        ),
        UsageType.TOTAL_RECRUITERS: UsageDetail(
            unlimited_use=True
        ),
    },
}

SUBSCRIPTION_FEATURE_DEFAULTS: dict[SubscriptionPlan, list[TierFeatures]] = {
    SubscriptionPlan.STARTER: [],
    SubscriptionPlan.PRO: [
        TierFeatures.PUBLIC_APPLICATION_PAGE,
        TierFeatures.EMAIL_INGRESS,
        TierFeatures.GENERATE_JOB_SKILLS,
        TierFeatures.GENERATE_JOB_QUESTIONS,
    ],
    SubscriptionPlan.ENTERPRISE: [
        TierFeatures.PUBLIC_APPLICATION_PAGE,
        TierFeatures.EMAIL_INGRESS,
        TierFeatures.GENERATE_JOB_SKILLS,
        TierFeatures.GENERATE_JOB_QUESTIONS,
    ],
}
