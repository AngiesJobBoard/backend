from datetime import datetime
from ajb.contexts.admin.companies.usecase import AdminCompanyUseCase
from ajb.contexts.billing.billing_models import SubscriptionPlan
from ajb.contexts.billing.subscriptions.models import CompanySubscription, CreateCompanySubscription, SubscriptionStatus
from ajb.contexts.companies.models import CreateCompany


def test_admin_create_company(request_scope):
    usecase = AdminCompanyUseCase(request_scope)

    # Create company with subscription
    company_object = CreateCompany(
        name="Test Company",
        slug="test",
        created_by_user="test",
        owner_email="test@email.com",
    )
    subscription_object = CreateCompanySubscription(
        company_id="test",
        plan=SubscriptionPlan.GOLD,
        start_date=datetime.now(),
        subscription_status=SubscriptionStatus.INACTIVE,
        usage_cost_details={},
        subscription_features=[],
        checkout_session=None,
    )
    usecase.create_company_with_subscription(company_object, subscription_object)