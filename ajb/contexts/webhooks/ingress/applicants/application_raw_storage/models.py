from dataclasses import dataclass
from pydantic import BaseModel
from ajb.base import BaseDataModel, PaginatedResponse


class CreateRawIngressApplication(BaseModel):
    company_id: str
    ingress_id: str
    application_id: str | None = None
    job_id: str | None = None
    data: dict


class RawIngressApplication(CreateRawIngressApplication, BaseDataModel): ...


@dataclass
class PaginatedRawApplication(PaginatedResponse[RawIngressApplication]):
    data: list[RawIngressApplication]
