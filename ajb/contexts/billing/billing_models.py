from enum import Enum
from pydantic import BaseModel


class SubscriptionPlan(str, Enum):
    """
    Starter is 0 per month then pay as you go
    Other plans progressively more expensive per month but marginally cheaper per action
    """

    SILVER = "Silver"
    GOLD = "Gold"
    PLATINUM = "Platinum"
    APPSUMO = "AppSumo"
    GOLD_TRIAL = "Gold Trial"


class UsageType(str, Enum):
    APPLICATIONS_PROCESSED = "applications_processed"
    TOTAL_JOBS = "total_jobs"
    TOTAL_RECRUITERS = "total_recruiters"


class UsageDetail(BaseModel):
    """
    If they have unlimited use, we don't check or charge for usage
    """

    free_tier_limit_per_month: int | None = None
    cost_usd_per_transaction: float = 0.0
    blocked_after_free_tier: bool = True
    unlimited_use: bool = False


class TierFeatures(str, Enum):
    ALL_FEATURES = "*"  # Special case for all features
    PUBLIC_APPLICATION_PAGE = "public_application_page"
    EMAIL_INGRESS = "email_ingress"
    API_INGRESS = "api_ingress"
    API_EGRESS = "api_egress"
    GENERATE_JOB_SKILLS = "generate_job_skills"
    GENERATE_JOB_QUESTIONS = "generate_job_questions"
    WHITE_LABELLING = "white_labelling"


SUBSCRIPTION_USAGE_COST_DETAIL_DEFAULTS: dict[
    SubscriptionPlan, dict[UsageType, UsageDetail]
] = {
    # 50 free applications per month then blocked. 5 jobs, only 1 recruiter - all blocked after free tier
    SubscriptionPlan.SILVER: {
        UsageType.APPLICATIONS_PROCESSED: UsageDetail(
            free_tier_limit_per_month=250,
        ),
        UsageType.TOTAL_JOBS: UsageDetail(
            free_tier_limit_per_month=5,
        ),
        UsageType.TOTAL_RECRUITERS: UsageDetail(
            free_tier_limit_per_month=1,
        ),
    },
    # 1000 free applications per month then 0.1 per application. 10 recruiters then 5 per recruiter per month, unlimited jobs
    SubscriptionPlan.GOLD: {
        UsageType.APPLICATIONS_PROCESSED: UsageDetail(
            free_tier_limit_per_month=1000,
            cost_usd_per_transaction=0.1,
            blocked_after_free_tier=False,
        ),
        UsageType.TOTAL_JOBS: UsageDetail(unlimited_use=True),
        UsageType.TOTAL_RECRUITERS: UsageDetail(
            free_tier_limit_per_month=10,
            cost_usd_per_transaction=5.0,
            blocked_after_free_tier=False,
        ),
    },
    # No limit plan
    SubscriptionPlan.PLATINUM: {
        UsageType.APPLICATIONS_PROCESSED: UsageDetail(free_tier_limit_per_month=3000),
        UsageType.TOTAL_JOBS: UsageDetail(unlimited_use=True),
        UsageType.TOTAL_RECRUITERS: UsageDetail(free_tier_limit_per_month=50),
    },
    SubscriptionPlan.APPSUMO: {
        UsageType.APPLICATIONS_PROCESSED: UsageDetail(free_tier_limit_per_month=500),
        UsageType.TOTAL_JOBS: UsageDetail(free_tier_limit_per_month=20),
        UsageType.TOTAL_RECRUITERS: UsageDetail(free_tier_limit_per_month=10),
    },
}

SUBSCRIPTION_FEATURE_DEFAULTS: dict[SubscriptionPlan, list[TierFeatures]] = {
    SubscriptionPlan.SILVER: [],
    SubscriptionPlan.GOLD: [
        TierFeatures.ALL_FEATURES,
    ],
    SubscriptionPlan.PLATINUM: [
        TierFeatures.ALL_FEATURES,
    ],
    SubscriptionPlan.APPSUMO: [
        TierFeatures.ALL_FEATURES,
    ],
}
