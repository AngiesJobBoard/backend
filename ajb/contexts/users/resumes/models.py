from dataclasses import dataclass
from pydantic import BaseModel

from ajb.base.models import BaseDataModel, PaginatedResponse


class UserCreateResume(BaseModel):
    file_type: str
    file_name: str
    resume_data: bytes


class CreateResume(BaseModel):
    remote_file_path: str
    resume_url: str
    file_name: str


class Resume(CreateResume, BaseDataModel): ...


@dataclass
class ResumePaginatedResponse(PaginatedResponse[Resume]):
    data: list[Resume]
