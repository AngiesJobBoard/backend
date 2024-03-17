from fastapi import APIRouter, Request, status, Depends

from ajb.base import RequestScope

from api.vendors import db


WEBHOOK_REQUEST_SCOPE = RequestScope(user_id="companies_webhook", db=db, company_id=None)


router = APIRouter(
    tags=["Webhooks"],
    prefix="/webhooks/companies",
)


@router.post("/jobs", status_code=status.HTTP_204_NO_CONTENT)
async def jobs_webhook_handler(request: Request):
    print(await request.json())
    return {"status": "ok"}


@router.post("/applicants", status_code=status.HTTP_204_NO_CONTENT)
async def applicants_webhook_handler(request: Request):
    print(await request.json())
    return {"status": "ok"}
