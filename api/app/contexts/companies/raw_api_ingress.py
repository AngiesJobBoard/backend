from fastapi import APIRouter, Request, Depends

from ajb.base import build_pagination_response, QueryFilterParams
from ajb.contexts.webhooks.ingress.applicants.application_raw_storage.repository import (
    RawIngressApplicationRepository,
)
from ajb.contexts.webhooks.ingress.applicants.application_raw_storage.models import (
    PaginatedRawApplication,
)
from api.middleware import scope

router = APIRouter(
    tags=["Raw API Ingress"], prefix="/companies/{company_id}/raw-ingress"
)


@router.get("/", response_model=PaginatedRawApplication)
def query_raw_ingress(
    request: Request, company_id: str, query: QueryFilterParams = Depends()
):
    results = RawIngressApplicationRepository(scope(request)).query(
        query, company_id=company_id
    )
    return build_pagination_response(
        results,
        query.page,
        query.page_size,
        request.url._url,
        PaginatedRawApplication,
    )
