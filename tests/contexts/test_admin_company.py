from ajb.contexts.admin.companies.models import (
    AdminUserCreateCompany,
    AdminUserCreateSubscription,
)
from ajb.contexts.admin.companies.usecase import AdminCompanyUseCase
from ajb.contexts.billing.billing_models import SubscriptionPlan
from ajb.contexts.billing.subscriptions.models import (
    SubscriptionStatus,
)
from ajb.contexts.billing.subscriptions.repository import CompanySubscriptionRepository
from ajb.contexts.companies.repository import CompanyRepository


def test_admin_create_company(request_scope):
    usecase = AdminCompanyUseCase(request_scope)

    # Prepare data
    company_object = AdminUserCreateCompany(
        name="Test Company", 
        owner_email="owner@test.com"
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
    company_subscription_repo = CompanySubscriptionRepository(request_scope, company.id)
    subscription = company_subscription_repo.get_most_recent()

    assert (
        subscription.subscription_status == SubscriptionStatus.ACTIVE
    )  # Ensure subscription is activated
    assert (
        subscription.plan == SubscriptionPlan.GOLD
    )  # Check subscription plan is correct
