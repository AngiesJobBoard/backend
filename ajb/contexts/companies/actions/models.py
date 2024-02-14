import typing as t
from dataclasses import dataclass
from pydantic import Field

from ajb.base import BaseDataModel, BaseAction, PaginatedResponse
from ajb.base.events import CompanyEvent


class CreateCompanyAction(BaseAction):
    action: CompanyEvent
    company_id: str
    candidate_user_id: str | None = None
    application_id: str | None = None
    position: int | None = None
    metadata: dict[str, t.Any] = Field(default_factory=dict)


class CompanyAction(BaseDataModel, CreateCompanyAction):
    ...


@dataclass
class PaginatedCompanyActions(PaginatedResponse[CompanyAction]):
    data: list[CompanyAction]
