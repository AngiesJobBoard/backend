from dataclasses import dataclass
from pydantic import BaseModel

from ajb.base.models import BaseDataModel, PaginatedResponse
from ajb.common.models import DataReducedCompany


class CreateSavedCompany(BaseModel):
    company_id: str


class SavedCompany(CreateSavedCompany, BaseDataModel):
    ...


class SavedCompaniesListObject(SavedCompany):
    company: DataReducedCompany


@dataclass
class SavedCompaniesPaginatedResponse(PaginatedResponse[SavedCompaniesListObject]):
    data: list[SavedCompaniesListObject]
