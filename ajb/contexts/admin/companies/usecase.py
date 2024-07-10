from datetime import datetime
from ajb.base.usecase import BaseUseCase
from ajb.contexts.admin.companies.models import (
    AdminUserCreateCompany,
    AdminUserCreateSubscription,
)
from ajb.contexts.billing.billing_models import TierFeatures
from ajb.contexts.billing.subscriptions.models import (
    CreateCompanySubscription,
    SubscriptionStatus,
)
from ajb.contexts.billing.subscriptions.repository import CompanySubscriptionRepository
from ajb.contexts.billing.usage.models import CreateMonthlyUsage
from ajb.contexts.billing.usage.repository import CompanySubscriptionUsageRepository
from ajb.contexts.billing.usecase.create_subscription_usage import (
    CreateSubscriptionUsage,
)
from ajb.contexts.companies.models import CreateCompany
from ajb.contexts.companies.repository import CompanyRepository


class AdminCompanyUseCase(BaseUseCase):
    def create_company_with_subscription(
        self, company: AdminUserCreateCompany, subscription: AdminUserCreateSubscription
    ):
        company_repo = CompanyRepository(self.request_scope)

        # Prepare company data
        company_data = CreateCompany(
            **company.model_dump(),
            created_by_user=self.request_scope.user_id,
        )

        # Create company
        created_company = company_repo.create(company_data)

        # Access subscription repositories
        company_subscription_repo = CompanySubscriptionRepository(
            self.request_scope, created_company.id
        )
        company_subscription_usage_repo = CompanySubscriptionUsageRepository(
            self.request_scope, created_company.id
        )

        # Determine subscription expiration
        usage_expiration = CreateSubscriptionUsage(
            self.request_scope
        )._get_usage_expiry(
            datetime.now(),
            subscription.plan,
        )
        subscription_expiration = subscription.end_date or usage_expiration

        # Create subscription
        company_subscription = CreateCompanySubscription(
            subscription_status=subscription.subscription_status,
            start_date=datetime.now(),
            company_id=created_company.id,
            plan=subscription.plan,
            end_date=subscription_expiration,
            checkout_session=None,
            usage_cost_details=subscription.usage_cost_details,
            subscription_features=subscription.subscription_features,
        )
        company_subscription_repo.create(company_subscription)

        # Create subscription usage
        company_subscription_usage_repo.create(
            CreateMonthlyUsage(
                company_id=created_company.id,
                usage_expires=usage_expiration,
                invoice_details=None,
            )
        )

        return created_company
