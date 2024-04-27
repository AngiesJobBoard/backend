import json
from fastapi import Request

from ajb.base import RequestScope
from ajb.contexts.companies.api_ingress_webhooks.models import (
    CompanyAPIIngress,
    APIIngressJWTData,
)
from ajb.contexts.companies.api_ingress_webhooks.repository import (
    CompanyAPIIngressRepository,
)
from ajb.contexts.companies.email_ingress_webhooks.repository import (
    CompanyEmailIngressRepository,
    CompanyEmailIngress,
)
from ajb.vendor.jwt import decode_jwt

from api.vendors import db, kafka_producer
from api.exceptions import Forbidden


async def verify_open_request(
    request: Request,
):
    authorization = request.headers["Authorization"]
    if "Bearer " in authorization:
        authorization = authorization.split("Bearer")[1].strip()
    if not authorization:
        raise Forbidden
    request.state.request_scope = RequestScope(
        user_id="webhook",
        db=db,
        kafka=kafka_producer,
    )


class OpenRequestValidator:
    def __init__(self, request: Request):
        self.request = request

    def validate_api_ingress_request(self) -> CompanyAPIIngress:
        authorization = self.request.headers["Authorization"]
        if "Bearer " in authorization:
            authorization = authorization.split("Bearer")[1].strip()
        company_id, token = authorization.split(":")

        # How to determine which source the data is coming from?
        # For now we will do the FILTHY option of pulling the first record if exists
        try:
            all_company_ingresses = CompanyAPIIngressRepository(
                self.request.state.request_scope, company_id=company_id
            ).get_all(company_id=company_id)
        except Exception as e:
            print(e)
            raise Forbidden

        if not all_company_ingresses:
            raise Forbidden

        company_ingress_record = all_company_ingresses[0]
        if not company_ingress_record.is_active:
            raise Forbidden

        # AJBTODO Other checks on allowed ip address or etc...
        try:
            token_data = APIIngressJWTData(
                **decode_jwt(token, company_ingress_record.secret_key)
            )
        except Exception as e:
            print(e)
            raise Forbidden
        assert token_data.company_id == company_id
        return company_ingress_record

    def validate_email_ingress_request(
        self,
        envelope: str,
    ) -> CompanyEmailIngress:
        json_loaded_envelope = json.loads(envelope)
        to_subdomain = json_loaded_envelope["to"][0].split("@")[0]
        company_ingress_record = CompanyEmailIngressRepository(
            self.request.state.request_scope
        ).get_one(subdomain=to_subdomain)
        if not company_ingress_record.is_active:
            raise Forbidden

        return company_ingress_record
