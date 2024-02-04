import typing as t
from enum import Enum


class ApplicationStatus(str, Enum):
    # Initial Submission
    SUBMITTED_FOR_ADMIN_REVIEW = "Submitted For Review"
    REJECTED_BY_ADMIN = "Rejected by Admin"
    RESUBMITTED_BY_USER = "Resubmitted by User"
    IN_REVIEW_BY_ADMIN = "In Review by Admin"

    # Company Review
    SUBMITTED_TO_COMPANY = "Submitted to Company"
    REJECTED_BY_COMPANY = "Rejected by Company"
    WITHDRAWN_BY_USER = "Withdrawn by User"
    COMPANY_IS_INTERVIEWING = "Company is Interviewing"

    # Company Offer
    COMPANY_HAS_OFFERED = "Company has created an Offer"
    OFFER_ACCEPTED_BY_USER = "Offer Accepted by User"
    USER_HIRED_BY_COMPANY = "User Hired by Company"
    USER_DECLINED_OFFER = "Offer Declined by User"
    ARCHIVED_BY_COMPANY = "Archived by Company"


USER_UPDATE = t.Type[
    t.Literal[
        ApplicationStatus.USER_DECLINED_OFFER,
        ApplicationStatus.OFFER_ACCEPTED_BY_USER,
        ApplicationStatus.WITHDRAWN_BY_USER,
    ]
]
