from fastapi import APIRouter, Request, Depends

from ajb.base import build_pagination_response
from ajb.contexts.admin.jobs.models import (
    AdminJobPostApproval,
    PaginatedApprovals,
    AdminCreateApprovalUpdate,
    JobApprovalStatus,
)
from ajb.contexts.companies.jobs.repository import JobRepository
from ajb.contexts.companies.jobs.models import (
    PaginatedJobsWithCompany,
    AdminSearchJobsWithCompany,
)
from ajb.contexts.admin.jobs.repository import AdminJobApprovalRepository
from ajb.contexts.admin.jobs.usecase import JobApprovalUseCase


router = APIRouter(tags=["Admin Jobs"], prefix="/admin/admin-jobs")


@router.get("/", response_model=PaginatedJobsWithCompany)
def get_jobs(
    request: Request,
    job_id: str | None = None,
    query: AdminSearchJobsWithCompany = Depends(),
    is_live: bool = False,
    is_boosted: bool = False,
):
    results = JobRepository(request.state.request_scope).get_jobs_with_company(
        job_id, query, is_live, is_boosted
    )
    return build_pagination_response(
        results, query.page, query.page_size, request.url._url, PaginatedJobsWithCompany
    )


@router.get("/approvals", response_model=PaginatedApprovals)
def get_all_job_approvals(
    request: Request,
    current_status: JobApprovalStatus | None = None,
    query: AdminSearchJobsWithCompany = Depends(),
):
    results = AdminJobApprovalRepository(request.state.request_scope).query_with_jobs(
        query, current_status
    )
    return build_pagination_response(
        results, query.page, query.page_size, request.url._url, PaginatedApprovals
    )


@router.get("/approvals/{id}", response_model=AdminJobPostApproval)
def get_job_approval_by_id(id: str, request: Request):
    return AdminJobApprovalRepository(request.state.request_scope).get_with_job(id)


@router.put("/approvals/{id}", response_model=AdminJobPostApproval)
def update_job_approval(id: str, request: Request, update: AdminCreateApprovalUpdate):
    return JobApprovalUseCase(request.state.request_scope).update_job_approval_status(
        id,
        user_id=request.state.request_scope.user_id,
        is_admin_update=True,
        updates=update,
    )
