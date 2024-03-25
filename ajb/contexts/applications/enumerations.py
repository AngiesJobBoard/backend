from enum import Enum


class ApplicationStatus(str, Enum):
    CREATED_BY_COMPANY = "Created by Company"
    LEFT_VOICEMAIL = "Left Voicemail"
    EMAILED = "Emailed"
    PHONE_INTERVIEW = "Phone Interview"
    IN_PERSON_INTERVIEW = "In Person Interview"
    DECLINED = "Declined"
    HIRED = "Hired"
