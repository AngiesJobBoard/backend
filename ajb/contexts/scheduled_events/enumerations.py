from enum import Enum


class ScheduledEventCategory(str, Enum):
    REPORT = "report"
    TASK = "task"
    EVENT = "event"


class ReportScheduledEvent(str, Enum):
    APPLICANT_SUMMARY = "applicant_summary"
