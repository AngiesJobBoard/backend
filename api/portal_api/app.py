from fastapi import APIRouter, Depends

from api.portal_api.contexts import (
    enumerations,
    health,
    static_data,
    users,
)
from api.portal_api.contexts.companies.app import company_api_router
from api.portal_api.middleware import verify_user

portal_api_router = APIRouter(
    tags=["Portal"],
    dependencies=[Depends(verify_user)],
)

portal_api_router.include_router(company_api_router)
portal_api_router.include_router(enumerations.router)
portal_api_router.include_router(health.router)
portal_api_router.include_router(static_data.router)
portal_api_router.include_router(users.router)
