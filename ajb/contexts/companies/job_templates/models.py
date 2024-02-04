from dataclasses import dataclass
from ajb.base.models import BaseDataModel, PaginatedResponse

from ..jobs.models import (
    UserCreateJob,
)


class UserCreateTemplate(UserCreateJob):
    template_name: str


class CreateJobTemplate(UserCreateTemplate):
    company_id: str


class JobTemplate(BaseDataModel, CreateJobTemplate): ...


@dataclass
class PaginatedJobTemplate(PaginatedResponse[JobTemplate]):
    data: list[JobTemplate]
