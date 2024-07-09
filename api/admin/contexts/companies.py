from fastapi import APIRouter, Depends, Request, Body

from ajb.base.models import QueryFilterParams, build_pagination_response
from ajb.contexts.admin.companies.usecase import AdminCompanyUseCase
from ajb.contexts.billing.billing_models import UsageType
from ajb.contexts.billing.subscriptions.models import CreateCompanySubscription
from ajb.contexts.billing.usecase.billing_usecase import CompanyBillingUsecase
from ajb.contexts.companies.invitations.models import Invitation, UserCreateInvitation
from ajb.contexts.companies.invitations.usecase import CompanyInvitationUseCase
from ajb.contexts.companies.models import Company, CreateCompany, RecruiterRole

from ajb.contexts.companies.recruiters.models import CreateRecruiter, PaginatedRecruiterAndUser, Recruiter, UserCreateRecruiter
from ajb.contexts.companies.recruiters.repository import RecruiterRepository
from ajb.exceptions import RecruiterCreateException, TierLimitHitException
from api.exceptions import GenericHTTPException, TierLimitHTTPException
from api.middleware import scope


router = APIRouter(tags=["Admin Create Company"], prefix="/companies")


@router.post("/", response_model=Company)
def admin_create_company(request: Request, company: CreateCompany = Body(...), subscription: CreateCompanySubscription = Body(...)):
    """Creates a new company with an active subscription"""
    return AdminCompanyUseCase(scope(request)).create_company_with_subscription(company, subscription)


@router.post("/{company_id}/recruiters", response_model=Recruiter)
def admin_create_recruiter(request: Request, company_id: str, email: str = Body(...)):
    """Adds a recruiter to a company"""
    try:
        response = CompanyInvitationUseCase(scope(request)).user_creates_invite(
            UserCreateInvitation(email=email, role=RecruiterRole.ADMIN), scope(request).user_id, company_id
        )
        return response
    except TierLimitHitException as e:
        raise TierLimitHTTPException()
    except RecruiterCreateException as e:
        raise GenericHTTPException(400, str(e))


@router.get("/{company_id}/recruiters", response_model=PaginatedRecruiterAndUser)
def admin_get_recruiters(
    request: Request, company_id: str, query: QueryFilterParams = Depends()
):
    """Gets all recruiters for a company"""
    results = RecruiterRepository(scope(request)).get_recruiters_by_company(
        company_id, query
    )
    return build_pagination_response(
        results,
        query.page,
        query.page_size,
        request.url._url,
        PaginatedRecruiterAndUser,
    )


@router.delete("/{recruiter_id}/recruiters")
def admin_delete_recruiter(request: Request, company_id: str, recruiter_id: str):
    """Deletes a recruiter from a company"""
    res = RecruiterRepository(scope(request)).delete(recruiter_id)
    CompanyBillingUsecase(scope(request)).increment_company_usage(
        company_id, UsageType.TOTAL_RECRUITERS, amount_to_increment=-1
    )
    return res