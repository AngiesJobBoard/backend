import pytest
from ajb.contexts.admin.companies.models import (
    AdminUserCreateCompany,
    AdminUserCreateSubscription,
)
from ajb.contexts.admin.companies.usecase import AdminCompanyUseCase
from ajb.contexts.billing.billing_models import SubscriptionPlan, TierFeatures
from ajb.contexts.billing.subscriptions.models import (
    SubscriptionStatus,
)
from ajb.contexts.billing.usecase.billing_usecase import CompanyBillingUsecase
from ajb.contexts.billing.validate_usage import (
    BillingValidateUsageUseCase,
    SubscriptionValidationError,
)
from ajb.contexts.companies.repository import CompanyRepository
from ajb.vendor.stripe.mock_repository import MockStripeRepository


def test_admin_create_company(request_scope):
    usecase = AdminCompanyUseCase(request_scope)

    # Prepare data
    company_object = AdminUserCreateCompany(
        name="Test Company", owner_email="owner@test.com"
    )
    subscription_object = AdminUserCreateSubscription(
        plan=SubscriptionPlan.GOLD,
        usage_cost_details={},
        subscription_features=[],
        subscription_status=SubscriptionStatus.ACTIVE,
    )

    # Create company with subscription
    company = usecase.create_company_with_subscription(
        company_object, subscription_object
    )

    # Validate company creation
    company_repo = CompanyRepository(request_scope)
    retrieved_company = company_repo.get(company.id)
    assert retrieved_company.name == company_object.name

    # Validate subscription creation
    mock_stripe = MockStripeRepository()
    billing = CompanyBillingUsecase(request_scope, stripe=mock_stripe)
    validator = BillingValidateUsageUseCase(
        request_scope, retrieved_company.id, billing
    )

    subscription = validator._get_company_subscription(retrieved_company.id)

    assert (
        subscription.subscription_status == SubscriptionStatus.ACTIVE
    )  # Ensure subscription is activated
    assert (
        subscription.plan == SubscriptionPlan.GOLD
    )  # Check subscription plan is correct


def test_admin_update_subscription(request_scope):
    usecase = AdminCompanyUseCase(request_scope)

    # Prepare data
    company_object = AdminUserCreateCompany(
        name="Test Company", owner_email="owner@test.com"
    )
    subscription_object = AdminUserCreateSubscription(
        plan=SubscriptionPlan.SILVER,
        usage_cost_details={},
        subscription_features=[],
        subscription_status=SubscriptionStatus.ACTIVE,
    )

    # Create company with subscription
    company = usecase.create_company_with_subscription(
        company_object, subscription_object
    )

    # Prepare subscription validator
    mock_stripe = MockStripeRepository()
    billing = CompanyBillingUsecase(request_scope, stripe=mock_stripe)

    # Validate that this current subscription doesn't have feature access
    with pytest.raises(SubscriptionValidationError):
        BillingValidateUsageUseCase(
            request_scope, company.id, billing
        ).validate_feature_access(TierFeatures.ALL_FEATURES)

    # Update to a new subscription with feature access
    new_subscription = AdminUserCreateSubscription(
        plan=SubscriptionPlan.GOLD,
        usage_cost_details={},
        subscription_features=[TierFeatures.ALL_FEATURES],
        subscription_status=SubscriptionStatus.ACTIVE,
    )
    usecase.update_company_subscription(company.id, new_subscription)

    # Validate that we now have feature access
    BillingValidateUsageUseCase(
        request_scope, company.id, billing
    ).validate_feature_access(TierFeatures.ALL_FEATURES)
