from dataclasses import dataclass
from pydantic import BaseModel

from ajb.base import BaseDataModel, PaginatedResponse


class CreateCoverLetter(BaseModel):
    cover_letter: str


class CoverLetter(CreateCoverLetter, BaseDataModel):
    ...


@dataclass
class CoverLetterPaginatedResponse(PaginatedResponse[CoverLetter]):
    data: list[CoverLetter]
