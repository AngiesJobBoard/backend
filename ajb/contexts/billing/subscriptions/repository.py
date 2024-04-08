from ajb.base import Collection, SingleChildRepository, RepositoryRegistry

from .models import CreateCompanySubscription, CompanySubscription


class CompanySubscriptionRepository(
    SingleChildRepository[CreateCompanySubscription, CompanySubscription]
):
    collection = Collection.COMPANY_SUBSCRIPTIONS
    entity_model = CompanySubscription

    def __init__(
        self,
        request_scope,
        company_id: str,
    ):
        super().__init__(request_scope, Collection.COMPANIES, company_id)
        self.company_id = company_id


RepositoryRegistry.register(CompanySubscriptionRepository)
