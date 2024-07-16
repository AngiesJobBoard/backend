from datetime import datetime
from ajb.base.usecase import BaseUseCase
from ajb.contexts.admin.companies.models import (
    AdminUserCreateCompany,
    AdminUserCreateSubscription,
)
from ajb.contexts.billing.subscriptions.models import (
    CreateCompanySubscription,
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

        # Determine usage expiration
        subscription_usage_creator = CreateSubscriptionUsage(self.request_scope)
        usage_expiration = subscription_usage_creator._get_usage_expiry(
            datetime.now(),
            subscription.plan,
        )

        # Create subscription usage
        created_usage = company_subscription_usage_repo.create(
            CreateMonthlyUsage(
                company_id=created_company.id,
                usage_expires=usage_expiration,
                invoice_details=None,
            )
        )

        # Create subscription
        subscription_expiration = subscription.end_date or usage_expiration
        company_subscription = self._transform_subscription_object(
            subscription, created_company.id, created_usage.id, subscription_expiration
        )

        company_subscription_repo.set_sub_entity(company_subscription)

        return created_company

    def update_company_subscription(
        self, company_id: str, new_subscription: AdminUserCreateSubscription
    ):
        company_repo = CompanyRepository(self.request_scope)

        # Retrieved requested company
        retrieved_company = company_repo.get(company_id)

        # Access subscription repositories
        company_subscription_repo = CompanySubscriptionRepository(
            self.request_scope, retrieved_company.id
        )
        company_subscription_usage_repo = CompanySubscriptionUsageRepository(
            self.request_scope, retrieved_company.id
        )

        # Determine new usage expiration
        subscription_usage_creator = CreateSubscriptionUsage(self.request_scope)
        usage_expiration = subscription_usage_creator._get_usage_expiry(
            datetime.now(),
            new_subscription.plan,
        )

        # Create new usage entry
        created_usage = company_subscription_usage_repo.create(
            CreateMonthlyUsage(
                company_id=retrieved_company.id,
                usage_expires=usage_expiration,
                invoice_details=None,
            )
        )

        # Update subscription repository
        subscription_expiration = new_subscription.end_date or usage_expiration
        company_subscription = self._transform_subscription_object(
            new_subscription,
            retrieved_company.id,
            created_usage.id,
            subscription_expiration,
        )

        company_subscription_repo.set_sub_entity(company_subscription)

    def _transform_subscription_object(
        self,
        subscription: AdminUserCreateSubscription,
        company_id: str,
        created_usage_id: str,
        subscription_expiration: datetime,
    ):
        return CreateCompanySubscription(
            subscription_status=subscription.subscription_status,
            start_date=datetime.now(),
            company_id=company_id,
            plan=subscription.plan,
            end_date=subscription_expiration,
            checkout_session=None,
            usage_cost_details=subscription.usage_cost_details,
            subscription_features=subscription.subscription_features,
            current_usage_id=created_usage_id,
        )
