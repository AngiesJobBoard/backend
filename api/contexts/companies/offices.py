from fastapi import APIRouter, Request, Depends

from ajb.base import QueryFilterParams, build_pagination_response
from ajb.contexts.companies.offices.models import (
    CreateOffice,
    Office,
    UserCreateOffice,
    UserUpdateOffice,
    PaginatedOffice,
)
from ajb.contexts.companies.offices.repository import OfficeRepository


router = APIRouter(tags=["Company Offices"], prefix="/companies/{company_id}/offices")


@router.get("/", response_model=PaginatedOffice)
def get_all_offices(
    request: Request, company_id: str, query: QueryFilterParams = Depends()
):
    """Gets all offices for a company"""
    results = OfficeRepository(
        request.state.request_scope, company_id
    ).get_all_by_company(query)
    return build_pagination_response(
        results, query.page, query.page_size, request.url._url, PaginatedOffice
    )


@router.get("/default", response_model=Office)
def get_default_office(request: Request, company_id: str):
    """Gets the default office for a company"""
    return OfficeRepository(
        request.state.request_scope, company_id
    ).get_default_office()


@router.get("/autocomplete")
def get_office_autocomplete(
    request: Request, company_id: str, prefix: str, field: str = "name"
):
    """Gets a list of offices that match the prefix"""
    return OfficeRepository(request.state.request_scope, company_id).get_autocomplete(
        field, prefix
    )


@router.post("/", response_model=Office)
def create_office(request: Request, company_id: str, office: UserCreateOffice):
    """Creates an office for a company"""
    return OfficeRepository(request.state.request_scope, company_id).create(
        CreateOffice(**office.model_dump(), company_id=company_id)
    )


@router.get("/{office_id}", response_model=Office)
def get_office(request: Request, company_id: str, office_id: str):
    """Gets an office for a company"""
    return OfficeRepository(request.state.request_scope, company_id).get(office_id)


@router.patch("/{office_id}", response_model=Office)
def update_office(
    request: Request, company_id: str, office_id: str, office: UserUpdateOffice
):
    """Updates an office for a company"""
    return OfficeRepository(request.state.request_scope, company_id).update(
        office_id, office
    )


@router.delete("/{office_id}")
def delete_office(request: Request, company_id: str, office_id: str):
    """Deletes an office for a company"""
    return OfficeRepository(request.state.request_scope, company_id).delete(office_id)
