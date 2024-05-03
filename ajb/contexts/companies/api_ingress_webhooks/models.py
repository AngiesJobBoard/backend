from enum import Enum
from dataclasses import dataclass
from datetime import datetime, timedelta
from pydantic import BaseModel, Field

from ajb.base import BaseDataModel, PaginatedResponse
from ajb.utils import generate_random_long_code, generate_random_short_code
from ajb.vendor.jwt import encode_jwt


class IngressSourceType(str, Enum):
    """ May 3 2024 - Currently only the company website is used for PCM but more are to be added"""
    COMPANY_WEBSITE = "company_website"


class APIIngressJWTData(BaseModel):
    company_id: str


class UserCreateIngress(BaseModel):
    integration_name: str
    source_type: IngressSourceType
    source: str


class UpdateIngress(BaseModel):
    integration_name: str | None = None
    allowed_ips: list[str] | None = None
    is_active: bool | None = None
    last_message_received: datetime | None = None


class CreateCompanyAPIIngress(UserCreateIngress):
    company_id: str
    secret_key: str
    salt: str
    expected_jwt: str
    allowed_ips: list[str] = Field(default_factory=list)
    is_active: bool = False
    last_message_received: datetime | None = None

    @classmethod
    def generate(
        cls,
        company_id: str,
        integration_name: str,
        source_type: IngressSourceType,
        source: str,
        is_active: bool,
    ) -> "CreateCompanyAPIIngress":
        secret_key = generate_random_long_code()
        salt = generate_random_short_code()
        partial_expected_jwt = encode_jwt(
            data=APIIngressJWTData(company_id=company_id).model_dump(),
            secret=secret_key,
            expiry=datetime.now() + timedelta(days=365),
        )
        expected_jwt = f"{company_id}:{partial_expected_jwt}:{salt}"
        return cls(
            company_id=company_id,
            integration_name=integration_name,
            secret_key=secret_key,
            salt=salt,
            expected_jwt=expected_jwt,
            source=source,
            source_type=source_type,
            is_active=is_active,
        )


class CompanyAPIIngress(CreateCompanyAPIIngress, BaseDataModel): ...


@dataclass
class PaginatedCompanyIngress(PaginatedResponse[CompanyAPIIngress]):
    data: list[CompanyAPIIngress]
