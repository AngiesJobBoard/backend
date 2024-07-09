from fastapi import APIRouter, Request, Body

from ajb.contexts.admin.companies.usecase import AdminCompanyUseCase
from ajb.contexts.billing.subscriptions.models import CreateCompanySubscription
from ajb.contexts.companies.models import Company, CreateCompany

from api.middleware import scope


router = APIRouter(tags=["Admin Create Company"], prefix="/create-company")


@router.post("/", response_model=Company)
def admin_create_company(request: Request, company: CreateCompany = Body(...), subscription: CreateCompanySubscription = Body(...)):
    return AdminCompanyUseCase(scope(request)).create_company_with_subscription(company, subscription)