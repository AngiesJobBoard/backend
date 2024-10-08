from pydantic import BaseModel

from ajb.base import BaseDataModel


class CreateAuditEvent(BaseModel):
    company_id: str | None
    type: str
    data: dict


class AuditEvent(CreateAuditEvent, BaseDataModel):
    pass
