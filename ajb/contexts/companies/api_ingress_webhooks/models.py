from dataclasses import dataclass
from datetime import datetime, timedelta
from pydantic import BaseModel, Field

from ajb.base import BaseDataModel, PaginatedResponse
from ajb.utils import generate_random_long_code
from ajb.vendor.jwt import encode_jwt


class APIIngressJWTData(BaseModel):
    company_id: str


class UserCreateIngress(BaseModel):
    integration_name: str
    source: str


class UpdateIngress(BaseModel):
    integration_name: str | None = None
    allowed_ips: list[str] | None = None
    is_active: bool | None = None
    last_message_received: datetime | None = None
    last_message: dict | None = None


class CreateCompanyAPIIngress(UserCreateIngress):
    company_id: str
    secret_key: str
    expected_jwt: str
    allowed_ips: list[str] = Field(default_factory=list)
    is_active: bool = False
    last_message_received: datetime | None = None
    last_message: dict | None = None

    @classmethod
    def generate(
        cls, company_id: str, integration_name: str, source: str, is_active: bool
    ) -> "CreateCompanyAPIIngress":
        secret_key = generate_random_long_code()
        partial_expected_jwt = encode_jwt(
            data=APIIngressJWTData(company_id=company_id).model_dump(),
            secret=secret_key,
            expiry=datetime.now() + timedelta(days=365),
        )
        expected_jwt = f"{company_id}:{partial_expected_jwt}"
        return cls(
            company_id=company_id,
            integration_name=integration_name,
            secret_key=secret_key,
            expected_jwt=expected_jwt,
            source=source,
            is_active=is_active,
        )


class CompanyAPIIngress(CreateCompanyAPIIngress, BaseDataModel): ...


@dataclass
class PaginatedCompanyIngress(PaginatedResponse[CompanyAPIIngress]):
    data: list[CompanyAPIIngress]
