from fastapi import APIRouter, Depends

from api.app.contexts import (
    enumerations,
    health,
    static_data,
    users,
)
from api.app.contexts.companies.app import company_api_router
from api.app.middleware import verify_user

portal_api_router = APIRouter(
    dependencies=[Depends(verify_user)],
)

portal_api_router.include_router(company_api_router)
portal_api_router.include_router(enumerations.router)
portal_api_router.include_router(health.router)
portal_api_router.include_router(static_data.router)
portal_api_router.include_router(users.router)
