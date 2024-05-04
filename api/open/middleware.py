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
from api.middleware import scope
from api.vendors import db, kafka_producer
from api.exceptions import Forbidden


async def verify_open_request(
    request: Request,
):
    # authorization = request.headers["Authorization"]
    # if "Bearer " in authorization:
    #     authorization = authorization.split("Bearer")[1].strip()
    # if not authorization:
    #     raise Forbidden
    request.state.request_scope = RequestScope(
        user_id="webhook",
        db=db,
        kafka=kafka_producer,
    )


class OpenRequestValidator:
    def __init__(self, request: Request):
        self.request = request

    def _get_company_ingress_record(
        self, authorization: str
    ) -> tuple[CompanyAPIIngress, str]:
        auth_parts = authorization.split(":")
        if len(auth_parts) == 3:
            company_id, token, salt = auth_parts
        else:
            raise Forbidden

        ingress_repo = CompanyAPIIngressRepository(
            scope(self.request), company_id=company_id
        )
        return ingress_repo.get_one(company_id=company_id, salt=salt), token

    def _validate_token_against_secret_key(
        self, token: str, company_id: str, secret_key: str
    ):
        token_data = APIIngressJWTData(**decode_jwt(token, secret_key))
        assert token_data.company_id == company_id

    def _validate_ip_addresses(self, ingress_record: CompanyAPIIngress):
        """
        incoming_ip_address = self.request.client.host if self.request.client else None
        assert incoming_ip_address in ingress_record.allowed_ips
        """
        pass

    def _run_all_validations(
        self, token: str, ingress_record: CompanyAPIIngress
    ) -> None:
        assert ingress_record.is_active
        self._validate_token_against_secret_key(
            token, ingress_record.company_id, ingress_record.secret_key
        )
        self._validate_ip_addresses(ingress_record)

    def validate_api_ingress_request(self) -> CompanyAPIIngress:
        authorization = self.request.headers["Authorization"]
        if "Bearer" in authorization:
            authorization = authorization.split("Bearer")[1].strip()

        company_ingress_record, token = self._get_company_ingress_record(authorization)
        try:
            self._run_all_validations(token, company_ingress_record)
        except Exception:
            raise Forbidden
        return company_ingress_record

    def validate_email_ingress_request(
        self,
        envelope: str,
    ) -> CompanyEmailIngress:
        json_loaded_envelope = json.loads(envelope)
        to_subdomain = json_loaded_envelope["to"][0].split("@")[0]
        company_ingress_record = CompanyEmailIngressRepository(
            scope(self.request)
        ).get_one(subdomain=to_subdomain)
        if not company_ingress_record.is_active:
            raise Forbidden

        return company_ingress_record
