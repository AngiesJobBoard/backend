from datetime import datetime

from ajb.contexts.billing.subscriptions.repository import CompanySubscriptionRepository
from ajb.contexts.billing.subscriptions.models import (
    CreateCompanySubscription,
    SubscriptionPlan,
)
from ajb.contexts.billing.billing_models import (
    SUBSCRIPTION_FREE_TIERS,
    SUBSCRIPTION_RATES,
)
from ajb.contexts.billing.usage.usecase import CompanySubscriptionUsageUsecase
from ajb.contexts.billing.usage.models import CreateMonthlyUsage

from ajb.fixtures.companies import CompanyFixture


def test_create_subscription(request_scope):
    company = CompanyFixture(request_scope).create_company()

    subscription_repo = CompanySubscriptionRepository(request_scope, company.id)
    created_subscription = subscription_repo.create(
        CreateCompanySubscription(
            company_id=company.id,
            plan=SubscriptionPlan.STARTER,
            start_date=datetime(2021, 1, 1),
            active=True,
            stripe_subscription_id="sub_123",
            rates=SUBSCRIPTION_RATES[SubscriptionPlan.STARTER],
            free_tier=SUBSCRIPTION_FREE_TIERS[SubscriptionPlan.STARTER],
        )
    )

    # AJBTODO some assertions or something


def test_monthly_usage(request_scope):
    company_fixture = CompanyFixture(request_scope)
    company = company_fixture.create_company()
    company_fixture.create_company_subscription(
        company.id, plan=SubscriptionPlan.STARTER
    )
    usecase = CompanySubscriptionUsageUsecase(request_scope)

    usage = CreateMonthlyUsage(
        company_id=company.id,
        resume_scans=10,
        match_scores=10,
        application_questions_answered=10,
        email_ingress=10,
        api_ingress=10,
        api_egress=10,
        resume_storage=10,
        total_recruiters=10,
    )

    created_usage = usecase.create_or_update_month_usage(
        company_id=company.id, usage=usage
    )
    assert created_usage.total_usage_usd == 0.0  # Because all within free tier

    # Now update usage with a lot

    new_usage = CreateMonthlyUsage(
        company_id=company.id,
        resume_scans=1000,
    )
    updated_usage = usecase.create_or_update_month_usage(
        company_id=company.id, usage=new_usage
    )

    assert updated_usage.resume_scans == 1010
    assert updated_usage.total_usage_usd == 950
