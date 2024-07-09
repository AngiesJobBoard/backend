from datetime import datetime
from ajb.base.usecase import BaseUseCase
from ajb.contexts.billing.subscriptions.models import CreateCompanySubscription, SubscriptionStatus
from ajb.contexts.billing.subscriptions.repository import CompanySubscriptionRepository
from ajb.contexts.billing.usage.models import CreateMonthlyUsage
from ajb.contexts.billing.usage.repository import CompanySubscriptionUsageRepository
from ajb.contexts.billing.usecase.create_subscription_usage import CreateSubscriptionUsage
from ajb.contexts.companies.models import CreateCompany
from ajb.contexts.companies.repository import CompanyRepository


class AdminCompanyUseCase(BaseUseCase):
    def create_company_with_subscription(self, company: CreateCompany, subscription: CreateCompanySubscription):
        company_repo = CompanyRepository(self.request_scope)

        # Create the company
        created_company = company_repo.create(data=company)
        company_subscription_repo = CompanySubscriptionRepository(self.request_scope, created_company.id)
        company_subscription_usage_repo = CompanySubscriptionUsageRepository(self.request_scope, created_company.id)

        # Create the subscription
        subscription.company_id = created_company.id # Update subscription with new company ID
        subscription.subscription_status = SubscriptionStatus.ACTIVE # Activate subscription
        company_subscription_repo.create(subscription)

        # Create subscription usage
        company_subscription_usage_repo.create(
            CreateMonthlyUsage(
                company_id=created_company.id,
                usage_expires=CreateSubscriptionUsage(self.request_scope)._get_usage_expiry(
                    subscription.start_date,
                    subscription.plan,
                ),
                invoice_details=None,
            )
        )

        return created_company