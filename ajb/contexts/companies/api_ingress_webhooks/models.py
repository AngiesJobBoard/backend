from datetime import datetime, timedelta
from pydantic import BaseModel, Field

from ajb.base import BaseDataModel
from ajb.utils import generate_random_long_code
from ajb.vendor.jwt import encode_jwt


class APIIngressJWTData(BaseModel):
    company_id: str


class CreateCompanyAPIIngress(BaseModel):
    company_id: str
    secret_key: str
    expected_jwt: str
    allowed_ips: list[str] = Field(default_factory=list)
    is_active: bool = False

    @classmethod
    def generate(cls, company_id: str) -> "CreateCompanyAPIIngress":
        secret_key = generate_random_long_code()
        partial_expected_jwt = encode_jwt(
            data=APIIngressJWTData(company_id=company_id).model_dump(),
            secret=secret_key,
            expiry=datetime.now() + timedelta(days=365)
        )
        expected_jwt = f"{company_id}:{partial_expected_jwt}"
        return cls(
            company_id=company_id,
            secret_key=secret_key,
            expected_jwt=expected_jwt
        )



class CompanyAPIIngress(CreateCompanyAPIIngress, BaseDataModel):
    ...
