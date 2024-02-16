from datetime import datetime
from fastapi import APIRouter, Depends, Request

from ajb.base import QueryFilterParams, build_pagination_response
from ajb.base.events import CompanyEvent
from ajb.contexts.companies.actions.repository import CompanyActionRepository
from ajb.contexts.companies.actions.models import PaginatedCompanyActions
from ajb.contexts.admin.search.repository import AdminSearchRepository
from ajb.contexts.admin.search.models import Aggregation


router = APIRouter(tags=["Admin Action Search"], prefix="/admin/actions")


@router.get("/companies", response_model=PaginatedCompanyActions)
def search_company_actions(
    request: Request,
    company_id: str | None = None,
    action_type: CompanyEvent | None = None,
    query: QueryFilterParams = Depends(),
):
    results = CompanyActionRepository(request.state.request_scope).query_event_type(
        company_id, action_type, query
    )
    return build_pagination_response(
        results, query.page, query.page_size, request.url._url, PaginatedCompanyActions
    )


@router.get("/companies-timeseries")
def search_company_actions_timeseries(
    request: Request,
    event: CompanyEvent | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
    aggregation: Aggregation | None = None,
):
    return AdminSearchRepository(
        request.state.request_scope
    ).get_action_timeseries_data(
        event=event,
        start=start,
        end=end,
        aggregation=aggregation,
        additional_groupbys=["action"],
    )
