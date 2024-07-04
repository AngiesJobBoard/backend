from datetime import datetime
import time
from ajb.contexts.billing.billing_models import SubscriptionPlan, TierFeatures
from ajb.contexts.billing.discount_codes.models import CodeType, CreateDiscountCode
from ajb.contexts.billing.discount_codes.repository import DiscountCodeRepository
from ajb.contexts.billing.usage.repository import CompanySubscriptionUsageRepository
from ajb.contexts.billing.usecase.billing_usecase import CompanyBillingUsecase
from ajb.contexts.billing.usecase.create_subscription_usage import (
    CreateSubscriptionUsage,
)
from ajb.contexts.billing.usecase.start_create_subscription import InvalidDiscountCode
from ajb.contexts.billing.usecase.start_update_subscription import (
    CannotUpdateSubscriptionException,
)
from ajb.contexts.billing.validate_usage import BillingValidateUsageUseCase
from ajb.fixtures.companies import CompanyFixture
from ajb.vendor.stripe.mock_repository import MockStripeRepository
from ajb.vendor.stripe.models import (
    InvoicePaymentSucceeded,
    StripeCheckoutSessionCompleted,
)

MOCK_PAYMENT = InvoicePaymentSucceeded(
    id="1",
    created=1622547800,
    effective_at=int(round(time.time())),
    amount_due=1000,
    amount_paid=1000,
    customer="1",
    customer_email="rcg@example.com",
    customer_name="recruiting guy",
    hosted_invoice_url="invoices.test.com",
    livemode=False,
    paid=True,
    status="paid",
    billing_reason="subscription_create",
    subscription="sub_1234567890",
)


def test_billing_usecases(request_scope):
    company_fixture = CompanyFixture(request_scope)
    company = company_fixture.create_company(create_subscription=False)
    mock_stripe = MockStripeRepository()
    billing = CompanyBillingUsecase(request_scope, stripe=mock_stripe)

    # Create trial subscription
    billing.start_create_subscription(
        company.id, SubscriptionPlan.GOLD_TRIAL, appsumo_code=""
    )
    assert (
        BillingValidateUsageUseCase(request_scope, company.id, billing)
        ._get_company_subscription(company.id)
        .plan
        == SubscriptionPlan.GOLD_TRIAL
    )

    # Errenously attempt to upgrade gold trial
    error_received = False
    try:
        billing.company_starts_update_subscription(
            company.id, SubscriptionPlan.PLATINUM
        )
    except CannotUpdateSubscriptionException:
        error_received = (
            True  # We are expecting to get this error as you can't upgrade a trial plan
        )

    assert (
        error_received is True
    ), "Attempting to upgrade a Gold Trial should have raised an CannotUpdateSubscriptionException"

    # Cancel current subscription
    billing.company_cancels_subscription(
        company.id, reason="Couldn't upgrade trial plan"
    )

    # Create subscription with AppSumo Code
    discount_code_repo = DiscountCodeRepository(request_scope)
    discount_code_repo.create(
        CreateDiscountCode(
            code="A12345678",
            discount=0,
            full_discount=True,
            code_type=CodeType.APP_SUMO,
        )
    )  # Create a valid discount code
    discount_code_repo.create(
        CreateDiscountCode(
            code="B12345678",
            discount=0,
            full_discount=True,
            has_been_used=True,
            code_type=CodeType.APP_SUMO,
        )
    )  # And a discount code that has already been used

    # Try to use an already redemmed AppSumo code
    error_received = False
    try:
        billing.start_create_subscription(
            company.id, SubscriptionPlan.APPSUMO, appsumo_code="B12345678"
        )
    except InvalidDiscountCode:
        error_received = True

    assert (
        error_received is True
    ), "Attempting to start an AppSumo subscription with invalid code should have raised a BadAppSumoCode exception"

    # Use a valid code to create the subscription
    billing.start_create_subscription(
        company.id, SubscriptionPlan.APPSUMO, appsumo_code="A12345678"
    )
    assert (
        BillingValidateUsageUseCase(request_scope, company.id, billing)
        ._get_company_subscription(company.id)
        .plan
        == SubscriptionPlan.APPSUMO
    )

    # Cancel subscription once again
    billing.company_cancels_subscription(company.id, reason="Switching to real plan")

    # Create gold subscription
    billing.start_create_subscription(
        company.id, SubscriptionPlan.GOLD, appsumo_code=""
    )
    billing.complete_create_subscription(
        StripeCheckoutSessionCompleted(**mock_stripe.create_session())
    )

    # "Pay for" subscription
    billing.company_completes_update_subscription(MOCK_PAYMENT)

    # Upgrade subscription to platinum
    billing.company_starts_update_subscription(company.id, SubscriptionPlan.PLATINUM)
    billing.company_completes_update_subscription(MOCK_PAYMENT)
    BillingValidateUsageUseCase(
        request_scope, company.id, billing
    ).validate_feature_access(TierFeatures.ALL_FEATURES)


def test_create_subscription_usage(request_scope):
    usage = CreateSubscriptionUsage(request_scope)
    company_fixture = CompanyFixture(request_scope)
    company = company_fixture.create_company()

    # Test invoice validation
    usage.validate_invoice(MOCK_PAYMENT)

    # Test run get usage expiry
    assert isinstance(
        usage._get_usage_expiry(datetime.now(), SubscriptionPlan.APPSUMO), datetime
    )
    assert isinstance(
        usage._get_usage_expiry(datetime.now(), SubscriptionPlan.GOLD), datetime
    )

    # Test usage creation
    usage.create_usage_from_paid_invoice(MOCK_PAYMENT)
    created_usage = CompanySubscriptionUsageRepository(
        request_scope, company.id
    ).get_all()[0]
    created_usage.company_id = company.id
