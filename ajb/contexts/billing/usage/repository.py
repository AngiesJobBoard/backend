from ajb.base import Collection, MultipleChildrenRepository, RepositoryRegistry

from .models import CreateMonthlyUsage, MonthlyUsage


class CompanySubscriptionUsageRepository(
    MultipleChildrenRepository[CreateMonthlyUsage, MonthlyUsage]
):
    collection = Collection.COMPANY_SUBSCRIPTION_USAGE_AND_BILLING
    entity_model = MonthlyUsage

    def __init__(self, request_scope, company_id: str):
        super().__init__(request_scope, Collection.COMPANIES, company_id)
        self.company_id = company_id


RepositoryRegistry.register(CompanySubscriptionUsageRepository)
