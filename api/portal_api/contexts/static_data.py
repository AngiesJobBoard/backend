from fastapi import APIRouter, Request, Depends

from ajb.base import QueryFilterParams, build_pagination_response
from ajb.contexts.static.models import (
    StaticDataTypes,
    StaticData,
    CreateStaticData,
    PaginatedStaticData,
)
from ajb.contexts.static.repository import StaticDataRepository
from ajb.contexts.static.view import StaticDataViewRepository
from api.middleware import scope


router = APIRouter(prefix="/static", tags=["static"])


@router.get("/", response_model=PaginatedStaticData)
def get_static_data(request: Request, query: QueryFilterParams = Depends()):
    response = StaticDataRepository(scope(request)).query(query)
    return build_pagination_response(
        response, query.page, query.page_size, request.url._url, PaginatedStaticData
    )


@router.post("/", response_model=StaticData)
def create_static_data(request: Request, data: CreateStaticData):
    return StaticDataRepository(scope(request)).create(data)


@router.get("/search")
def search_static_data(
    request: Request, type: StaticDataTypes, search: str | None = None, limit: int = 5
):
    return StaticDataViewRepository(scope(request)).basic_search(
        type=type, search=search, limit=limit
    )


@router.get("/types")
def get_static_data_types():
    return [item.value for item in StaticDataTypes]


@router.get("/{id}", response_model=StaticData)
def get_static_data_by_id(request: Request, id: str):
    return StaticDataRepository(scope(request)).get(id)


@router.put("/{id}", response_model=StaticData)
def update_static_data(request: Request, id: str, data: CreateStaticData):
    return StaticDataRepository(scope(request)).update(id, data)


@router.delete("/{id}")
def delete_static_data(request: Request, id: str):
    return StaticDataRepository(scope(request)).delete(id)
