from fastapi import APIRouter, Request, status, Depends

from ajb.base import RequestScope

from api.vendors import db


WEBHOOK_REQUEST_SCOPE = RequestScope(user_id="companies_webhook", db=db, company_id=None)


async def verify_webhook_event(request: Request) -> dict:
    return await request.json()


router = APIRouter(
    tags=["Webhooks"],
    prefix="/webhooks/companies",
    dependencies=[Depends(verify_webhook_event)],
)


@router.post("/jobs", status_code=status.HTTP_204_NO_CONTENT)
async def jobs_webhook_handler(payload: dict, company_id: str):
    print(payload)


@router.post("/applicants", status_code=status.HTTP_204_NO_CONTENT)
async def applicants_webhook_handler(payload: dict, company_id: str):
    print(payload)
