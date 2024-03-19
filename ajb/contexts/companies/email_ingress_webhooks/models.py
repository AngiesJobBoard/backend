from datetime import datetime, timedelta
from enum import Enum
from pydantic import BaseModel, Field

from ajb.base import BaseDataModel
from ajb.utils import generate_random_short_code


class EmailIngressType(str, Enum):
    CREATE_JOB = "CREATE_JOB"
    CREATE_APPLICATION = "CREATE_APPLICATION"


class CreateCompanyEmailIngress(BaseModel):
    company_id: str
    subdomain: str
    expires_at: datetime = datetime.now() + timedelta(days=365)
    ingress_type: EmailIngressType
    allowed_email_domains: list[str] = Field(default_factory=list)
    allowed_email_addresses: list[str] = Field(default_factory=list)
    is_active: bool = False

    @classmethod
    def generate(cls, company_id: str, ingress_type: EmailIngressType) -> "CreateCompanyEmailIngress":
        random_subdomain = generate_random_short_code(length=16)
        return cls(company_id=company_id, subdomain=random_subdomain, ingress_type=ingress_type)


class CompanyEmailIngress(CreateCompanyEmailIngress, BaseDataModel):
    ...
