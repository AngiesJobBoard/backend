from typing import Literal
from fastapi import APIRouter, Request, Depends

from ajb.base import BaseTimeseriesData
from ajb.contexts.admin.search.repository import AdminSearchRepository
from ajb.contexts.admin.search.models import (
    AdminSearch,
    AdminTimeseriesSearch,
)
from ajb.contexts.users.models import PaginatedUsers
from ajb.contexts.users.repository import UserRepository
from ajb.contexts.companies.models import CompanyPaginatedResponse
from ajb.contexts.companies.repository import CompanyRepository
from ajb.contexts.companies.jobs.repository import JobRepository
from ajb.contexts.companies.jobs.models import (
    PaginatedJobsWithCompany,
    AdminSearchJobsWithCompany,
)
from ajb.contexts.applications.repository import CompanyApplicationRepository
from ajb.contexts.applications.models import PaginatedAdminApplicationView
from ajb.base import (
    PaginatedResponse,
    build_pagination_response,
    QueryFilterParams,
    Collection,
)
from api.exceptions import GenericHTTPException


router = APIRouter(tags=["Admin Search"], prefix="/admin")


@router.get("/search", response_model=PaginatedResponse)
def search(request: Request, query: AdminSearch = Depends()):
    results = AdminSearchRepository(request.state.request_scope).admin_search(query)
    return build_pagination_response(
        results, query.page, query.page_size, request.url._url
    )


@router.get("/count")
def count(request: Request, query: AdminSearch = Depends()):
    return AdminSearchRepository(request.state.request_scope).admin_count(query)


@router.get("/timeseries", response_model=BaseTimeseriesData)
def search_timeseries(request: Request, query: AdminTimeseriesSearch = Depends()):
    results = AdminSearchRepository(request.state.request_scope).get_timeseries_data(
        collection=query.collection,
        start=query.start,
        end=query.end,
        aggregation=query.aggregation,
        filters=query.filters,
    )
    return results


@router.get("/global")
def global_search(request: Request, text: str, page: int = 0, page_size: int = 5):
    return AdminSearchRepository(request.state.request_scope).admin_global_text_search(
        text, page, page_size
    )


@router.get("/object/{collection}/{object_id}")
def get_object(request: Request, collection: Collection, object_id: str):
    res = AdminSearchRepository(request.state.request_scope).get_object(
        collection, object_id
    )
    if not res:
        raise GenericHTTPException(status_code=404, detail="Object not found")
    return res


@router.get("/search/search-companies", response_model=CompanyPaginatedResponse)
def admin_search_companies(request: Request, query: QueryFilterParams = Depends()):
    results = CompanyRepository(request.state.request_scope).query(query)
    return build_pagination_response(
        results, query.page, query.page_size, request.url._url, CompanyPaginatedResponse
    )


@router.get("/search/search-users", response_model=PaginatedUsers)
def admin_search_users(request: Request, query: QueryFilterParams = Depends()):
    results = UserRepository(request.state.request_scope).query(query)
    return build_pagination_response(
        results, query.page, query.page_size, request.url._url, PaginatedUsers
    )


@router.get("/search/search-jobs", response_model=PaginatedJobsWithCompany)
def admin_search_jobs(request: Request, query: AdminSearchJobsWithCompany = Depends()):
    results = JobRepository(request.state.request_scope).get_jobs_with_company(
        query=query
    )
    return build_pagination_response(
        results, query.page, query.page_size, request.url._url, PaginatedJobsWithCompany
    )


@router.get("/search/search-applications", response_model=PaginatedAdminApplicationView)
def admin_search_applications(request: Request, query: QueryFilterParams = Depends()):
    results = CompanyApplicationRepository(
        request.state.request_scope
    ).get_admin_application_view(repo_filters=query)
    return build_pagination_response(
        results,
        query.page,
        query.page_size,
        request.url._url,
        PaginatedAdminApplicationView,
    )
