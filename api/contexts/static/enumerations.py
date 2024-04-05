from fastapi import APIRouter
from fastapi.responses import JSONResponse

from ajb.common.models import ExperienceLevel, JobLocationType
from ajb.contexts.companies.enumerations import (
    NumEmployeesEnum,
    ScheduleType,
    WeeklyScheduleType,
    ShiftType,
    JobContractLength,
    ResumeRequirement,
)
from ajb.contexts.scheduled_events.enumerations import (
    ScheduledEventCategory,
    ReportScheduledEvent,
)
from ajb.static.enumerations import (
    LevelOfEducationEnum,
    RaceEnum,
    GenderEnum,
    LanguageProficiencyEnum,
    PayType,
)

router = APIRouter(prefix="/static/enumerations", tags=["Enumerations"])


@router.get("/company")
def get_company_enums():
    return JSONResponse(
        content={
            "num_employees": [
                num_employees.value for num_employees in NumEmployeesEnum
            ],
            "experience_level": [
                experience_level.value for experience_level in ExperienceLevel
            ],
            "schedule_type": [schedule_type.value for schedule_type in ScheduleType],
            "weekly_schedule_type": [
                weekly_schedule_type.value
                for weekly_schedule_type in WeeklyScheduleType
            ],
            "shift_type": [shift_type.value for shift_type in ShiftType],
            "job_location_type": [
                job_location_type.value for job_location_type in JobLocationType
            ],
            "job_contract_length": [
                job_contract_length.value for job_contract_length in JobContractLength
            ],
            "pay_type": [pay_type.value for pay_type in PayType],
            "resume_requirement": [
                resume_requirement.value for resume_requirement in ResumeRequirement
            ],
        }
    )


@router.get("/scheduled-events")
def get_scheduled_event_enums():
    return JSONResponse(
        content={
            "category": [category.value for category in ScheduledEventCategory],
            "report": [report.value for report in ReportScheduledEvent],
        }
    )


@router.get("/user")
def get_user_enums():
    return JSONResponse(
        content={
            "level_of_education": [
                level_of_education.value for level_of_education in LevelOfEducationEnum
            ],
            "race": [race.value for race in RaceEnum],
            "gender": [gender.value for gender in GenderEnum],
            "language_proficiency": [
                language_proficiency.value
                for language_proficiency in LanguageProficiencyEnum
            ],
        }
    )
