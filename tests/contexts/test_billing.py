from datetime import datetime

from ajb.contexts.billing.subscriptions.repository import CompanySubscriptionRepository
from ajb.contexts.billing.subscriptions.models import (
    CreateCompanySubscription,
    SubscriptionPlan,
    UserUpdateCompanySubscription,
)
from ajb.contexts.billing.billing_models import (
    SUBSCRIPTION_USAGE_COST_DETAIL_DEFAULTS,
    UsageType,
)
from ajb.contexts.billing.usecase import CompanyBillingUsecase
from ajb.contexts.billing.usage.models import CreateMonthlyUsage

from ajb.contexts.companies.repository import CompanyRepository
from ajb.fixtures.companies import CompanyFixture

from ajb.vendor.stripe.mock_repository import MockStripeRepository


def test_create_and_update_subscription(request_scope):
    company = CompanyFixture(request_scope).create_company()
    usecase = CompanyBillingUsecase(request_scope)

    # Create subscription
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

    # Validate subscription creation
    subscription = usecase.get_or_create_company_subscription(company.id)
    assert (
        subscription.plan == SubscriptionPlan.STARTER
    )  # Ensure that the starter plan has been applied as above

    # Upgrade company to pro plan
    subscription_update = UserUpdateCompanySubscription(plan=SubscriptionPlan.PRO)
    usecase.update_company_subscription(company.id, subscription_update)

    # Validate subscription update
    subscription = usecase.get_or_create_company_subscription(company.id)
    assert (
        subscription.plan == SubscriptionPlan.PRO
    )  # Ensure that the pro plan has been selected


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
        },
    )

    created_usage = usecase.create_or_update_month_usage(
        company_id=company.id, usage=usage
    )
    assert int(created_usage.total_usage_usd) == 0  # Because all within free tier

    # Now update usage with a lot

    new_usage = CreateMonthlyUsage(
        company_id=company.id, transaction_counts={UsageType.RESUME_SCANS: 1000}
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
        },
    )

    created_usage = usecase.create_or_update_month_usage(
        company_id=company.id, usage=usage
    )
    assert int(created_usage.total_usage_usd) == 0  # Because all within free tier

    updated_usage = usecase.increment_company_usage(
        company_id=company.id,
        incremental_usages={
            UsageType.RESUME_SCANS: 1000,
            UsageType.MATCH_SCORES: 1000,
        },
    )

    queried_updated_usage = usecase.get_or_create_company_usage(company.id)

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
        },
    )
    usecase.create_or_update_month_usage(company_id=company.id, usage=usage)
    usecase.increment_company_usage(
        company_id=company.id,
        incremental_usages={
            UsageType.RESUME_SCANS: -5,
        },
    )

    queried_updated_usage = usecase.get_or_create_company_usage(company.id)
    assert queried_updated_usage.transaction_counts[UsageType.RESUME_SCANS] == 5


def test_increment_company_usage_no_plan_no_usage(request_scope):
    company_fixture = CompanyFixture(request_scope)
    company = company_fixture.create_company()

    usecase = CompanyBillingUsecase(request_scope)
    usecase.increment_company_usage(
        company_id=company.id,
        incremental_usages={
            UsageType.RESUME_SCANS: 10,
        },
    )

    created_plan = usecase.get_or_create_company_subscription(company.id)
    created_usage = usecase.get_or_create_company_usage(company.id)

    assert created_plan.plan == SubscriptionPlan.STARTER
    assert created_usage.transaction_counts[UsageType.RESUME_SCANS] == 10
    assert int(created_usage.total_usage_usd) == 0


def test_get_company_name_with_id(request_scope):
    company_fixture = CompanyFixture(request_scope)
    company = company_fixture.create_company()

    usecase = CompanyBillingUsecase(request_scope)

    returned_company_id = usecase._get_company_name_with_id(company)
    assert isinstance(returned_company_id, str)  # Returned value has to be a string
    assert company.name in returned_company_id  # Must contain company name
    assert str(company.id) in returned_company_id  # Must contain company ID


def test_stripe_setup(request_scope):
    company_fixture = CompanyFixture(request_scope)
    company_repo = CompanyRepository(request_scope)
    company = company_fixture.create_company()

    usecase = CompanyBillingUsecase(request_scope, MockStripeRepository())

    # Run to create company stripe information
    assert (
        company.stripe_customer_id is None
    )  # Make sure we're starting with no stripe ID
    retrieved_company = usecase._get_or_update_company_with_created_stripe_company_id(
        company.id
    )
    assert isinstance(
        retrieved_company.stripe_customer_id, str
    )  # Ensure that the company was assigned an ID successfully

    # Test that it is retrieving cached information rather than creating a new stripe ID
    company_repo.update_fields(
        company.id, stripe_customer_id="1234"  # Set a custom stripe ID
    )
    retrieved_company = usecase._get_or_update_company_with_created_stripe_company_id(
        company.id
    )
    assert (
        retrieved_company.stripe_customer_id == "1234"
    )  # Ensure that our custom ID wasn't overwritten


def test_billing_period_conversion(request_scope):
    usecase = CompanyBillingUsecase(request_scope)

    testing_dates = [
        ("2024-01", "January 2024"),
        ("2023-12", "December 2023"),
        ("2022-06", "June 2022"),
    ]

    # Test the conversion for a few different dates
    for input_date, expected_output in testing_dates:
        assert (
            usecase._convert_billing_period_to_date_range(input_date) == expected_output
        )


def test_convert_usage_to_stripe_invoice(request_scope):
    company_fixture = CompanyFixture(request_scope)
    company = company_fixture.create_company()

    usecase = CompanyBillingUsecase(request_scope, MockStripeRepository())

    # Prepare company data
    company_usage = usecase.get_or_create_company_usage(
        company.id
    )  # We'll start with an empty company usage
    company_subscription = usecase.get_or_create_company_subscription(company.id)
    assert company.stripe_customer_id is None  # We shouldn't have a stripe ID yet

    # Run method with no stripe ID, this should raise an exception
    passed_with_no_stripe_id = True  # Flag to keep track
    try:
        usecase.convert_usage_to_stripe_invoice_data(
            company, company_subscription, company_usage
        )
    except ValueError:
        passed_with_no_stripe_id = False

    if passed_with_no_stripe_id:
        raise AssertionError(
            "convert_usage_to_stripe_invoice_data ran with no stripe ID"
        )

    # Assign stripe ID and test the function
    company = usecase._get_or_update_company_with_created_stripe_company_id(
        company.id
    )  # Assign stripe ID
    invoice = usecase.convert_usage_to_stripe_invoice_data(
        company, company_subscription, company_usage
    )

    # Try again with company usage
    usecase.increment_company_usage(
        company_id=company.id,
        incremental_usages={
            UsageType.RESUME_SCANS: 1000,
        },
    )
    company_usage = usecase.get_or_create_company_usage(company.id)
    invoice = usecase.convert_usage_to_stripe_invoice_data(
        company, company_subscription, company_usage
    )

    assert (
        invoice.stripe_customer_id == company.stripe_customer_id
    )  # Make sure we have the right customer ID on the invoice
    assert (
        len(invoice.invoice_items) == 1
    )  # We should have one item on our invoice (the resume scans)


def test_generate_stripe_invoice(request_scope):
    company_fixture = CompanyFixture(request_scope)
    company = company_fixture.create_company()

    usecase = CompanyBillingUsecase(request_scope, MockStripeRepository())

    # Run with no usage data to ensure that doesn't throw an error
    usecase.generate_stripe_invoice(company.id)

    # Add some data so that an invoice is generated
    usecase.increment_company_usage(
        company_id=company.id,
        incremental_usages={
            UsageType.RESUME_SCANS: 1000,
        },
    )

    # Run it again with usage data
    usecase.generate_stripe_invoice(company.id)
