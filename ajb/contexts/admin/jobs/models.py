from dataclasses import dataclass
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field

from ajb.base import BaseDataModel, PaginatedResponse
from ajb.common.models import DataReducedCompany, DataReducedJob
from ajb.contexts.companies.jobs.models import Job
from ajb.contexts.companies.models import Company


class JobApprovalStatus(str, Enum):
    RESUBMITTED = "RESUBMITTED"  # Any time the user submits again
    PENDING = "PENDING"  # After user submits job first time
    IN_REVIEW = "IN REVIEW"  # When admin takes in review
    APPROVED = "APPROVED"  # Ready to post
    REJECTED = "REJECTED"  # Job can not be posted
    POSTED = "POSTED"  # Job is posted
    UNPOSTED = "UNPOSTED"  # Job is unposted
    REMOVED_BY_USER = "REMOVED BY USER"  # Job is removed by user


class CreateAdminJobPostApproval(BaseModel):
    company_id: str
    job_id: str
    requesting_user: str


class AdminCreateApprovalUpdate(BaseModel):
    approval_status: JobApprovalStatus
    reason: str


class UpdateJobApprovalStatus(AdminCreateApprovalUpdate):
    updated_by_id: str
    user_is_admin: bool
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class AdminJobPostApproval(BaseDataModel, CreateAdminJobPostApproval):
    current_approval_status: JobApprovalStatus = JobApprovalStatus.PENDING
    current_reason: str = ""
    history: list[UpdateJobApprovalStatus] = Field(default_factory=list)

    job: Job | None = None
    company: Company | None = None


class DataReducedAdminJobPostApproval(BaseDataModel, CreateAdminJobPostApproval):
    current_approval_status: JobApprovalStatus = JobApprovalStatus.PENDING
    current_reason: str = ""
    history: list[UpdateJobApprovalStatus] = Field(default_factory=list)

    job: DataReducedJob | None = None
    company: DataReducedCompany | None = None


@dataclass
class PaginatedApprovals(PaginatedResponse[DataReducedAdminJobPostApproval]):
    data: list[DataReducedAdminJobPostApproval]
