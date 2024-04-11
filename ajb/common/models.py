from enum import Enum
from datetime import datetime
from pydantic import BaseModel, root_validator

from ajb.vendor.google_maps import get_lat_long_from_address
from ajb.static.enumerations import PayType
from ajb.utils import get_nested_value

from ajb.base import BaseAction, BaseDataModel


def get_google_string(values: dict) -> str:
    address_line_1 = values.get("address_line_1", "")
    address_line_2 = values.get("address_line_2", "")
    city = values.get("city", "")
    state = values.get("state", "")
    zipcode = values.get("zipcode", "")
    country = values.get("country", "")

    address = f"{address_line_1} {address_line_2}".strip()
    return f"{address} {city} {state} {zipcode} {country}".strip()


class Location(BaseModel):
    address_line_1: str | None = None
    address_line_2: str | None = None
    zipcode: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    lat: float | None = None
    lng: float | None = None

    @root_validator(pre=True)
    def update_lat_lon(cls, values):
        lat, lng = values.get("lat"), values.get("lng")
        if lat is None or lng is None:
            address_string = get_google_string(values)
            if not address_string:
                return values
            try:
                new_lat, new_lng = get_lat_long_from_address(address_string)
                values["lat"] = new_lat
                values["lng"] = new_lng
            except IndexError:
                pass
        return values


class FileUpload(BaseModel):
    file_type: str
    file_name: str
    file_data: bytes


def convert_pay_to_hourly(pay_amount: float, pay_type: PayType) -> float:
    if pay_type == PayType.HOURLY:
        return pay_amount
    if pay_type == PayType.DAILY:
        return round(pay_amount / 8, 2)
    if pay_type == PayType.WEEKLY:
        return round(pay_amount / 40, 2)
    if pay_type == PayType.MONTHLY:
        return round(pay_amount / 160, 2)
    if pay_type == PayType.YEARLY:
        return round(pay_amount / 2080, 2)
    raise ValueError(f"Invalid pay type: {pay_type}")


class Pay(BaseModel):
    pay_type: PayType = PayType.YEARLY
    pay_min: int | None = None
    pay_max: int | None = None
    exact_pay: int | None = None
    additional_metadata: dict[str, str] | None = None

    @property
    def min_pay_as_hourly(self) -> float:
        if not self.pay_min:
            return 0
        return convert_pay_to_hourly(self.pay_min, self.pay_type)

    @property
    def max_pay_as_hourly(self) -> float:
        if not self.pay_max:
            return 0
        return convert_pay_to_hourly(self.pay_max, self.pay_type)


class ExperienceLevel(str, Enum):
    no_experience = "No Experience"
    under_one_year = "Under 1 Year"
    one_year = "1 Year"
    two_years = "2 Years"
    three_years = "3 Years"
    five_years = "5 Years"
    ten_years = "10 Years"
    eleven_or_more_years = "11+ Years"


class JobLocationType(str, Enum):
    REMOTE = "Remote"
    IN_OFFICE = "In Office"
    HYBRID = "Hybrid"
    ON_THE_ROAD = "On the Road"


class DataReducedJob(BaseDataModel):
    """Used to reduce the amount of data returned when querying for approvals"""

    position_title: str | None = None
    description: str | None = None
    industry_category: str | None = None
    pay: Pay | None = None
    desired_start_date: datetime | None = None
    job_main_image: str | None = None
    job_icon: str | None = None
    experience_required: ExperienceLevel | None = None
    job_score: int | None = None


class DataReducedCompany(BaseDataModel):
    """Used to reduce the amount of data returned when querying for approvals"""

    name: str | None = None
    main_image: str | None = None
    icon_image: str | None = None


class JobNameOnly(BaseModel):
    position_title: str


class DataReducedUser(BaseDataModel):
    """Used to return a subset of user information, mostly for admin purposes"""

    first_name: str | None = None
    last_name: str | None = None
    image_url: str | None = None
    phone_number: str | None = None
    email: str | None = None
    auth_id: str | None = None
    profile_is_public: bool | None = None
    candidate_score: float | None = None
    created_at: datetime | None = None
    most_recent_job: str | None = None
    most_recent_company: str | None = None
    desired_job_title: str | None = None

    @classmethod
    def from_db_record(cls, record: dict):
        most_recent_job = get_nested_value(
            record, ["qualifications", "most_recent_job", "job_title"]
        )
        most_recent_company = get_nested_value(
            record, ["qualifications", "most_recent_job", "company_name"]
        )
        return cls(
            id=record["id"],
            created_at=record["created_at"],
            updated_at=record["updated_at"],
            created_by=record["created_by"],
            updated_by=record["updated_by"],
            first_name=record.get("first_name"),
            last_name=record.get("last_name"),
            image_url=record.get("image_url"),
            phone_number=record.get("phone_number"),
            email=record.get("email"),
            auth_id=record.get("auth_id"),
            profile_is_public=record.get("profile_is_public"),
            candidate_score=record.get("candidate_score"),
            most_recent_job=str(most_recent_job) if most_recent_job else None,
            most_recent_company=(
                str(most_recent_company) if most_recent_company else None
            ),
            desired_job_title=record.get("job_preferences", {}).get(
                "desired_job_title"
            ),
        )


class TimeRange(BaseModel):
    start: datetime | None = None
    end: datetime | None = None


class TimesSeriesAverage(str, Enum):
    RAW = "raw"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"

    def get_datetime_format(self):
        return {
            TimesSeriesAverage.RAW: "%Y-%m-%d %H:%M:%S",
            TimesSeriesAverage.HOURLY: "%Y-%m-%d %H:00:00",
            TimesSeriesAverage.DAILY: "%Y-%m-%d 00:00:00",
        }[self]


class PreferredTone(Enum):
    professional = "Professional"
    concise = "Concise"
    friendly = "Friendly"
    formal = "Formal"
    excited = "Excited"
    funny = "Funny"


def get_actions_as_daily_timeseries(
    actions: list[BaseAction], averaging: TimesSeriesAverage
) -> dict[str, dict[datetime, int]]:
    output: dict[str, dict[str, int]] = {}
    for action in actions:
        action_date = action.created_at.strftime(averaging.get_datetime_format())

        if averaging == TimesSeriesAverage.RAW:
            output[action.action.value][action_date] = 1
            continue

        if action.action.value not in output:
            output[action.action.value] = {}

        if action_date not in output[action.action.value]:
            output[action.action.value][action_date] = 0

        output[action.action.value][action_date] += 1
    return {
        action_type: {
            datetime.strptime(date, averaging.get_datetime_format()): count
            for date, count in action_timeseries.items()
        }
        for action_type, action_timeseries in output.items()
    }


class QuestionStatus(str, Enum):
    PENDING_ANSWER = "Pending Answer"
    ANSWERED = "Answered"
    FAILED = "Failed"


class AnswerEnum(str, Enum):
    YES = "Yes"
    NO = "No"
    UNSURE = "Unsure"


class ApplicationQuestion(BaseModel):
    """
    Users can create a set of questions that are answered from information on an application
    They will be answered with "yes", "no", or "unsure"
    """

    question: str
    question_status: QuestionStatus = QuestionStatus.PENDING_ANSWER
    answer: AnswerEnum | None = None
    confidence: int | None = None
    reasoning: str | None = None
    error_text: str | None = None
