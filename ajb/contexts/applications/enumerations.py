import typing as t
from enum import Enum


class ApplicationStatus(str, Enum):
    # Company Offer
    CREATED_BY_COMPANY = "Created by Company"
    COMPANY_HAS_OFFERED = "Company has created an Offer"
    OFFER_ACCEPTED_BY_USER = "Offer Accepted by User"
    USER_HIRED_BY_COMPANY = "User Hired by Company"
    USER_DECLINED_OFFER = "Offer Declined by User"
    ARCHIVED_BY_COMPANY = "Archived by Company"
    REJECTED_BY_COMPANY = "Rejected by Company"


USER_UPDATE = t.Type[
    t.Literal[
        ApplicationStatus.USER_DECLINED_OFFER,
        ApplicationStatus.OFFER_ACCEPTED_BY_USER,
    ]
]
