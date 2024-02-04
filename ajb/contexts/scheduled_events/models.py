from datetime import datetime
from pydantic import BaseModel
from croniter import croniter

from ajb.base.models import BaseDataModel

from .enumerations import ScheduledEventCategory


class CreateScheduledEvent(BaseModel):
    related_object_id: str
    name: str
    description: str
    cron: str
    event_category: ScheduledEventCategory
    event_type: str  # Any of the enums below, verified by scheduling service
    last_run_time: datetime | None = None
    next_run_time: datetime | None = None
    is_active: bool = True

    def calculate_next_invocation(self):
        cron = croniter(self.cron, datetime.utcnow())
        return cron.get_next(datetime)


class UpdateScheduledEvent(BaseModel):
    name: str | None = None
    description: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    cron: str | None = None
    is_active: bool | None = None


class ScheduledEvent(BaseDataModel, CreateScheduledEvent):
    id: str
