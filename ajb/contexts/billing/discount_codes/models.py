from datetime import datetime, timedelta
from enum import Enum
from pydantic import BaseModel

from ajb.base import BaseDataModel
from ajb.utils import generate_random_long_code


class CodeType(str, Enum):
    APP_SUMO = "app_sumo"


class CreateDiscountCode(BaseModel):
    code: str
    discount: float
    full_discount: bool
    has_been_used: bool = False
    code_type: CodeType
    expires: datetime | None = None

    @classmethod
    def generate_code(
        cls, code_type: CodeType = CodeType.APP_SUMO, expires: datetime | None = None
    ) -> "CreateDiscountCode":
        return cls(
            code=generate_random_long_code(),
            discount=0,
            full_discount=True,
            code_type=code_type,
            expires=expires,
        )


class DiscountCode(CreateDiscountCode, BaseDataModel):
    pass
