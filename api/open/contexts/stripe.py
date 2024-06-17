from fastapi import APIRouter, Request, status, Depends

from ajb.base import RequestScope
from api.vendors import db, kafka_producer


WEBHOOK_REQUEST_SCOPE = RequestScope(
    user_id="stripe_webhook", db=db, kafka=kafka_producer
)


async def verify_stripe_webhook_event(request: Request) -> dict:
    # AJBTODO More validation later...
    return await request.json()


router = APIRouter(
    tags=["Webhooks"],
    prefix="/webhooks/stripe",
    dependencies=[Depends(verify_stripe_webhook_event)],
)


@router.post("/payments", status_code=status.HTTP_204_NO_CONTENT)
async def payments_webhook_handler(payload: dict):
    print(payload)
    return status.HTTP_204_NO_CONTENT
