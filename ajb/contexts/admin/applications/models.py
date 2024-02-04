from enum import Enum
from pydantic import BaseModel


class ApplicationApprovalStatus(str, Enum):
    PENDING = "PENDING"  # After user submits application first time
    IN_REVIEW = "IN REVIEW"  # When admin takes in review
    APPROVED = "APPROVED"  # Admin has approved, goes to company
    REJECTED = "REJECTED"  # Admin has not approved, does not go to company


class CreateAdminApplicationApproval(BaseModel):
    company_id: str
    job_id: str
    application_id: str
    application_user_id: str


class AdminCreateApplicationApprovalUpdate(BaseModel):
    approval_status: ApplicationApprovalStatus
    reason: str
