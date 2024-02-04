from fastapi import APIRouter, Request, Depends

from ajb.vendor.algolia.models import (
    AlgoliaSearchResults,
)
from ajb.contexts.search.companies.search_repository import CompanySearchRepository
from ajb.contexts.search.companies.models import (
    CompanySearchContext,
    CompanySearchParams,
    AlgoliaCompanySearchResults,
    Company,
)

from api.vendors import search_companies


router = APIRouter(tags=["Search"], prefix="/search/companies")


@router.get("/", response_model=AlgoliaCompanySearchResults)
def search_companies_endpoint(request: Request, query: CompanySearchParams = Depends()):
    """Searches for companies"""
    context = CompanySearchContext(user_id=request.state.request_scope.user_id)
    return CompanySearchRepository(
        request.state.request_scope,
        search_companies,
    ).search(context, query)


@router.get("/autocomplete", response_model=AlgoliaSearchResults)
def companies_autocomplete(query: str):
    """Autocompletes a company search"""
    return search_companies.autocomplete(query, ["name"])


@router.get("/{company_id}", response_model=Company)
def get_company(request: Request, company_id: str):
    """Gets a company by id"""
    return CompanySearchRepository(
        request.state.request_scope,
        search_companies,
    ).get_company(company_id)
