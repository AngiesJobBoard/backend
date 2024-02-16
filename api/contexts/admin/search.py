from fastapi import APIRouter, Request, Depends

from ajb.common.models import DataReducedUser
from ajb.contexts.admin.search.repository import AdminSearchRepository
from ajb.contexts.admin.search.models import (
    PaginatedDataReducedUser,
    AdminSearch,
    AdminTimeseriesSearch,
)
from ajb.contexts.users.repository import UserRepository
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


@router.get("/timeseries", response_model=tuple[list[dict], int])
def search_timeseries(request: Request, query: AdminTimeseriesSearch = Depends()):
    results = AdminSearchRepository(request.state.request_scope).get_timeseries_data(
        collection=query.collection,
        start=query.start,
        end=query.end,
        aggregation=query.aggregation,
    )
    return results


@router.get("/global")
def global_search(request: Request, text: str, page: int = 0, page_size: int = 5):
    return AdminSearchRepository(request.state.request_scope).admin_global_text_search(
        text, page, page_size
    )


@router.get("/search/users", response_model=PaginatedDataReducedUser)
def search_users(request: Request, query: QueryFilterParams = Depends()):
    """A helper route for admins searching for users"""
    results, count = UserRepository(request.state.request_scope).query(query)
    formatted_results = [
        DataReducedUser.from_db_record(result.model_dump()) for result in results
    ]
    return build_pagination_response(
        (formatted_results, count),
        query.page,
        query.page_size,
        request.url._url,
        PaginatedDataReducedUser,
    )


@router.get("/object/{collection}/{object_id}")
def get_object(request: Request, collection: Collection, object_id: str):
    res = AdminSearchRepository(request.state.request_scope).get_object(
        collection, object_id
    )
    if not res:
        raise GenericHTTPException(status_code=404, detail="Object not found")
    return res
