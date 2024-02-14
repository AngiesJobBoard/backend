from dataclasses import dataclass
from pydantic import BaseModel

from ajb.base.models import BaseDataModel, PaginatedResponse
from ajb.common.models import DataReducedCompany, DataReducedJob


class CreateSavedJob(BaseModel):
    job_id: str
    company_id: str


class SavedJob(CreateSavedJob, BaseDataModel):
    ...


class SavedJobsListObject(SavedJob):
    job: DataReducedJob
    company: DataReducedCompany


@dataclass
class SavedJobsPaginatedResponse(PaginatedResponse[SavedJobsListObject]):
    data: list[SavedJobsListObject]
