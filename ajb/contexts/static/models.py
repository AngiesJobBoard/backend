from enum import Enum
from dataclasses import dataclass
from pydantic import BaseModel

from ajb.base import BaseDataModel, PaginatedResponse


class StaticDataTypes(str, Enum):
    BENEFITS = "benefits"
    SKILLS = "skills"
    INDUSTRIES = "industries"
    LANGUAGES = "languages"
    FIELD_OF_STUDY = "field_of_study"
    CERTIFICATIONS = "certifications"
    LICENSES = "licenses"


class CreateStaticData(BaseModel):
    name: str
    description: str | None = None
    type: StaticDataTypes


class StaticData(CreateStaticData, BaseDataModel): ...


@dataclass
class PaginatedStaticData(PaginatedResponse[StaticData]):
    data: list[StaticData]
