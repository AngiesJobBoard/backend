from cachetools import TTLCache
from fastapi import APIRouter, Request, Depends

from ajb.base import QueryFilterParams, build_pagination_response
from ajb.base.constants import BaseConstants
from ajb.common.models import TimeRange, TimesSeriesAverage
from ajb.contexts.companies.dashboard.models import (
    CompanyDashboardSummary,
    PaginatedDashboardApplicants,
    PaginatedCompanyDashboardJobs,
    CompanyDashboardJobPostStatistics,
)
from ajb.contexts.companies.dashboard.usecase import CompanyDashboardUseCase
from ajb.vendor.arango.models import Operator


router = APIRouter(
    tags=["Company Dashboards"], prefix="/companies/{company_id}/dashboard"
)


SUMMARY_CACHE = TTLCache(maxsize=1024, ttl=60)


@router.get("/summary", response_model=CompanyDashboardSummary)
def get_company_dashboard_summary(
    request: Request, company_id: str, hard_refresh: bool = False
):
    """Gets the summary of a company's dashboard"""
    if hard_refresh:
        SUMMARY_CACHE.pop(company_id, None)

    if company_id in SUMMARY_CACHE:
        return SUMMARY_CACHE[company_id]

    summary = CompanyDashboardUseCase(
        request.state.request_scope, company_id
    ).get_company_dashboard_summary()
    SUMMARY_CACHE[company_id] = summary
    return summary


@router.get("/applicants", response_model=PaginatedDashboardApplicants)
def get_company_dashboard_applicants(
    request: Request,
    company_id: str,
    time_range: TimeRange = Depends(),
    query: QueryFilterParams = Depends(),
):
    results = CompanyDashboardUseCase(
        request.state.request_scope, company_id, time_range
    ).get_company_dashboard_applicants(query.convert_to_repo_filters())
    return build_pagination_response(
        results,
        query.page,
        query.page_size,
        request.url._url,
        PaginatedDashboardApplicants,
    )


@router.get("/jobs", response_model=PaginatedCompanyDashboardJobs)
def get_company_dashboard_jobs(
    request: Request,
    company_id: str,
    time_range: TimeRange = Depends(),
    query: QueryFilterParams = Depends(),
):
    results = CompanyDashboardUseCase(
        request.state.request_scope, company_id, time_range
    ).get_company_dashboard_job_posts(query.convert_to_repo_filters())
    return build_pagination_response(
        results,
        query.page,
        query.page_size,
        request.url._url,
        PaginatedCompanyDashboardJobs,
    )


@router.get("/job-statistics", response_model=CompanyDashboardJobPostStatistics)
def get_company_dashboard_job_statistics(
    request: Request,
    company_id: str,
    time_range: TimeRange = Depends(),
    averaging: TimesSeriesAverage = TimesSeriesAverage.HOURLY,
    query: QueryFilterParams = Depends(),
):
    return CompanyDashboardUseCase(
        request.state.request_scope, company_id, time_range, averaging=averaging
    ).get_company_job_post_statistics(query.convert_to_repo_filters())
