from fastapi import APIRouter, Depends

from api.open.contexts import clerk, companies
from api.open.middleware import verify_open_request

open_router = APIRouter(
    tags=["Open"],
    prefix="/open",
    dependencies=[Depends(verify_open_request)],
)

open_router.include_router(clerk.router)
open_router.include_router(companies.router)
