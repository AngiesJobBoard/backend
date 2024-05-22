"""
-- Scratch notes on this auth --


user sends us some header like 555:abc123 (which is always the same for all webhooks into our system)
the 555 is the company ID so we lookup the API ingress from the company ID (it is a single child type repo)
From there, we get the record which includes the generated secret used to encode the header and we decrypt this JWT
now we have a decode dict like this 
{company id: asd}
which we can use to compare against the payload being sent

"""

from ajb.base import (
    Collection,
    MultipleChildrenRepository,
    RepositoryRegistry,
    RequestScope,
    RepoFilterParams,
    QueryFilterParams,
)
from ajb.vendor.jwt import decode_jwt

from .models import CreateCompanyAPIIngress, CompanyAPIIngress, APIIngressJWTData


class CompanyAPIIngressRepository(
    MultipleChildrenRepository[CreateCompanyAPIIngress, CompanyAPIIngress]
):
    collection = Collection.COMPANY_API_INGRESS_WEBHOOKS
    entity_model = CompanyAPIIngress

    def __init__(self, request_scope: RequestScope, company_id: str):
        super().__init__(
            request_scope,
            parent_collection=Collection.COMPANIES.value,
            parent_id=company_id,
        )

    @classmethod
    def validate_webhook_jwt(
        cls,
        request_scope: RequestScope,
        received_encoded_jwt: str,
        company_id_being_accessed: str,
    ):
        jwt_company_id, jwt = received_encoded_jwt.split(":")
        this_repo = cls(request_scope, jwt_company_id)
        ingress_record = this_repo.get_sub_entity()
        decoded_jwt_data = APIIngressJWTData(
            **decode_jwt(jwt, ingress_record.secret_key)
        )
        assert decoded_jwt_data.company_id == company_id_being_accessed


RepositoryRegistry.register(CompanyAPIIngressRepository)
