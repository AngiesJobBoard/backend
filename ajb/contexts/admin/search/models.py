from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from pydantic import BaseModel

from ajb.base import Collection, QueryFilterParams, PaginatedResponse
from ajb.common.models import DataReducedUser


class AdminSearch(QueryFilterParams):
    collection: Collection
    start: datetime | None = None
    end: datetime | None = None
    page_size: int = 10000


@dataclass
class PaginatedDataReducedUser(PaginatedResponse[DataReducedUser]):
    data: list[DataReducedUser]


class Aggregation(Enum):
    RAW = None
    MINUTE = "minute"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"

    def get_datetime_format(self):
        return {
            Aggregation.RAW: "%yyyy-%mm-%ddT%hh:%ii",
            Aggregation.MINUTE: "%yyyy-%mm-%ddT%hh:%ii",
            Aggregation.HOURLY: "%yyyy-%mm-%ddT%hh",
            Aggregation.DAILY: "%yyyy-%mm-%dd",
            Aggregation.WEEKLY: "%yyyy-W%kk",
            Aggregation.MONTHLY: "%yyyy-%mm",
            Aggregation.YEARLY: "%yyyy",
        }[self]


class AdminTimeseriesSearch(BaseModel):
    collection: Collection
    start: datetime | None = None
    end: datetime | None = None
    aggregation: Aggregation = Aggregation.RAW
