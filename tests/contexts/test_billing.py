from datetime import datetime

from ajb.contexts.billing.subscriptions.repository import CompanySubscriptionRepository
from ajb.contexts.billing.subscriptions.models import (
    CreateCompanySubscription,
    SubscriptionPlan,
)
from ajb.contexts.billing.billing_models import (
    SUBSCRIPTION_USAGE_COST_DETAIL_DEFAULTS,
    UsageType
)
from ajb.contexts.billing.usecase import CompanyBillingUsecase
from ajb.contexts.billing.usage.models import CreateMonthlyUsage

from ajb.fixtures.companies import CompanyFixture


def test_create_subscription(request_scope):
    company = CompanyFixture(request_scope).create_company()

    subscription_repo = CompanySubscriptionRepository(request_scope, company.id)
    subscription_repo.create(
        CreateCompanySubscription(
            company_id=company.id,
            plan=SubscriptionPlan.STARTER,
            start_date=datetime(2021, 1, 1),
            stripe_subscription_id="sub_123",
            usage_cost_details=SUBSCRIPTION_USAGE_COST_DETAIL_DEFAULTS[
                SubscriptionPlan.STARTER
            ],
        )
    )

    # AJBTODO some assertions or something


def test_monthly_usage(request_scope):
    company_fixture = CompanyFixture(request_scope)
    company = company_fixture.create_company()
    company_fixture.create_company_subscription(
        company.id, plan=SubscriptionPlan.STARTER
    )
    usecase = CompanyBillingUsecase(request_scope)

    usage = CreateMonthlyUsage(
        company_id=company.id,
        transaction_counts={
            UsageType.RESUME_SCANS: 10,
            UsageType.MATCH_SCORES: 10,
            UsageType.APPLICATION_QUESTIONS_ANSWERED: 10,
            UsageType.EMAIL_INGRESS: 10,
            UsageType.API_INGRESS: 10,
            UsageType.API_EGRESS: 10,
            UsageType.TOTAL_RECRUITERS: 10,
        }
    )

    created_usage = usecase.create_or_update_month_usage(
        company_id=company.id, usage=usage
    )
    assert created_usage.total_usage_usd == 0.0  # Because all within free tier

    # Now update usage with a lot

    new_usage = CreateMonthlyUsage(
        company_id=company.id,
        transaction_counts={
            UsageType.RESUME_SCANS: 1000
        }
    )
    updated_usage = usecase.create_or_update_month_usage(
        company_id=company.id, usage=new_usage
    )

    assert updated_usage.transaction_counts[UsageType.RESUME_SCANS] == 1010
    assert updated_usage.total_usage_usd == 960


def test_increment_monthly_usage(request_scope):
    company_fixture = CompanyFixture(request_scope)
    company = company_fixture.create_company()
    company_fixture.create_company_subscription(
        company.id, plan=SubscriptionPlan.STARTER
    )
    usecase = CompanyBillingUsecase(request_scope)

    usage = CreateMonthlyUsage(
        company_id=company.id,
        transaction_counts={
            UsageType.RESUME_SCANS: 10,
            UsageType.MATCH_SCORES: 10,
            UsageType.APPLICATION_QUESTIONS_ANSWERED: 10,
            UsageType.EMAIL_INGRESS: 10,
            UsageType.API_INGRESS: 10,
            UsageType.API_EGRESS: 10,
            UsageType.TOTAL_RECRUITERS: 10,
        }
    )

    created_usage = usecase.create_or_update_month_usage(
        company_id=company.id, usage=usage
    )
    assert created_usage.total_usage_usd == 0.0  # Because all within free tier

    updated_usage = usecase.increment_company_usage(
        company_id=company.id,
        incremental_usages={
            UsageType.RESUME_SCANS: 1000,
            UsageType.MATCH_SCORES: 1000,
        }
    )

    queried_updated_usage = usecase.get_or_create_company_current_usage(company.id)

    assert updated_usage == queried_updated_usage
    assert updated_usage.total_usage_usd == 1920
    assert updated_usage.transaction_counts[UsageType.RESUME_SCANS] == 1010
    assert updated_usage.transaction_counts[UsageType.MATCH_SCORES] == 1010


def test_decrement_monthly_usage(request_scope):
    company_fixture = CompanyFixture(request_scope)
    company = company_fixture.create_company()
    company_fixture.create_company_subscription(
        company.id, plan=SubscriptionPlan.STARTER
    )
    usecase = CompanyBillingUsecase(request_scope)
    usage = CreateMonthlyUsage(
        company_id=company.id,
        transaction_counts={
            UsageType.RESUME_SCANS: 10,
        }
    )
    usecase.create_or_update_month_usage(
        company_id=company.id, usage=usage
    )
    usecase.increment_company_usage(
        company_id=company.id,
        incremental_usages={
            UsageType.RESUME_SCANS: -5,
        }
    )

    queried_updated_usage = usecase.get_or_create_company_current_usage(company.id)
    assert queried_updated_usage.transaction_counts[UsageType.RESUME_SCANS] == 5


def test_increment_company_usage_no_plan_no_usage(request_scope):
    company_fixture = CompanyFixture(request_scope)
    company = company_fixture.create_company()

    usecase = CompanyBillingUsecase(request_scope)
    usecase.increment_company_usage(
        company_id=company.id,
        incremental_usages={
            UsageType.RESUME_SCANS: 10,
        }
    )

    created_plan = usecase.get_or_create_company_subscription(company.id)
    created_usage = usecase.get_or_create_company_current_usage(company.id)

    assert created_plan.plan == SubscriptionPlan.STARTER
    assert created_usage.transaction_counts[UsageType.RESUME_SCANS] == 10
    assert created_usage.total_usage_usd == 0.0
