from fastapi import APIRouter

from api.open.contexts import clerk, companies, job_applications, stripe

open_router = APIRouter()

open_router.include_router(clerk.router)
open_router.include_router(companies.router)
open_router.include_router(job_applications.router)
open_router.include_router(stripe.router)
