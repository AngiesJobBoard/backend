from fastapi import APIRouter, Request, Depends

from ajb.base import QueryFilterParams, build_pagination_response
from ajb.contexts.companies.models import RecruiterRole
from ajb.contexts.companies.recruiters.repository import RecruiterRepository
from ajb.contexts.companies.recruiters.models import (
    PaginatedRecruiterAndUser,
    RecruiterAndUser,
)
from ajb.contexts.billing.usage.usecase import (
    CompanySubscriptionUsageUsecase,
    UsageType,
)


router = APIRouter(
    tags=["Company Recruiters"], prefix="/companies/{company_id}/recruiters"
)


@router.get("/", response_model=PaginatedRecruiterAndUser)
def get_company_recruiters(
    request: Request, company_id: str, query: QueryFilterParams = Depends()
):
    """Gets all recruiters for a company"""
    results = RecruiterRepository(
        request.state.request_scope
    ).get_recruiters_by_company(company_id, query)
    return build_pagination_response(
        results,
        query.page,
        query.page_size,
        request.url._url,
        PaginatedRecruiterAndUser,
    )


@router.get("/{recruiter_id}", response_model=RecruiterAndUser)
def get_company_recruiter(request: Request, recruiter_id: str):
    """Gets a recruiter for a company"""
    return RecruiterRepository(request.state.request_scope).get_recruiter_by_id(
        recruiter_id
    )


@router.patch("/{recruiter_id}", response_model=RecruiterAndUser)
def update_recruiter_role(request: Request, recruiter_id: str, new_role: RecruiterRole):
    """Updates a recruiter role"""
    repo = RecruiterRepository(request.state.request_scope)
    repo.update_fields(recruiter_id, role=new_role)
    return repo.get_recruiter_by_id(recruiter_id)


@router.delete("/{recruiter_id}")
def delete_recruiter(request: Request, company_id: str, recruiter_id: str):
    """Deletes a recruiter"""
    res = RecruiterRepository(request.state.request_scope).delete(recruiter_id)
    CompanySubscriptionUsageUsecase(
        request.state.request_scope
    ).increment_company_usage(
        company_id=company_id,
        incremental_usages={
            UsageType.TOTAL_RECRUITERS: -1,
        },
    )
    return res
