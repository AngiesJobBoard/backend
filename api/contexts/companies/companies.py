from fastapi import APIRouter, Request

from ajb.contexts.companies.models import (
    Company,
    UserCreateCompany,
    UpdateCompany,
    CompanyNameAndID,
    CompanyGlobalSearchResults,
)
from ajb.contexts.companies.repository import CompanyRepository
from ajb.contexts.companies.usecase import CompaniesUseCase
from ajb.exceptions import CompanyCreateException

from api.vendors import mixpanel
from api.exceptions import GenericHTTPException


router = APIRouter(tags=["Companies"], prefix="/companies")


@router.get("/", response_model=list[CompanyNameAndID])
def get_all_companies(request: Request):
    """Gets all companies"""
    # Not paginated for now because a single user isn't likely to have that many companies
    return CompaniesUseCase(request.state.request_scope).get_companies_by_user(
        request.state.request_scope.user_id
    )


@router.post("/", response_model=Company)
def create_company(request: Request, company: UserCreateCompany):
    try:
        response = CompaniesUseCase(request.state.request_scope).user_create_company(
            company, request.state.request_scope.user_id
        )
        mixpanel.company_created(
            request.state.request_scope.user_id, response.id, response.name
        )
        return response
    except CompanyCreateException as exc:
        raise GenericHTTPException(status_code=400, detail=str(exc))


@router.get("/{company_id}/global-search", response_model=CompanyGlobalSearchResults)
def get_company_global_search(
    request: Request, company_id: str, text: str, page: int = 0, page_size: int = 5
):
    """Gets a list of jobs, applications, or (soon) recruiters from a company"""
    return CompaniesUseCase(
        request.state.request_scope
    ).get_company_global_search_results(company_id, text, page, page_size)


@router.patch("/{company_id}", response_model=Company)
def update_company(request: Request, company_id: str, company: UpdateCompany):
    return CompanyRepository(request.state.request_scope).update(company_id, company)


@router.get("/{company_id}", response_model=Company)
def get_company(request: Request, company_id: str):
    """Gets a company by id"""
    return CompanyRepository(request.state.request_scope).get(company_id)


@router.delete("/{company_id}")
def delete_company(request: Request, company_id: str):
    """Deletes a company by id"""
    return CompanyRepository(request.state.request_scope).delete(company_id)
