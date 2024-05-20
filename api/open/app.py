from fastapi import APIRouter

from api.open.contexts import clerk, companies, job_applications

open_router = APIRouter(
    tags=["Open"],
)

open_router.include_router(clerk.router)
open_router.include_router(companies.router)
open_router.include_router(job_applications.router)
