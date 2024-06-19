from fastapi import APIRouter, Request, status, Depends

from ajb.base import RequestScope
from ajb.contexts.billing.billing_event_router import StripeBillingEventRouter
from api.vendors import db, kafka_producer


WEBHOOK_REQUEST_SCOPE = RequestScope(
    user_id="stripe_webhook", db=db, kafka=kafka_producer
)


async def verify_stripe_webhook_event(request: Request) -> dict:
    # AJBTODO More validation later...
    # Stripe sends us a signature in the header that we can use to verify the payload
    return await request.json()


router = APIRouter(
    tags=["Webhooks"],
    prefix="/webhooks/stripe",
    dependencies=[Depends(verify_stripe_webhook_event)],
)


@router.post("/payments", status_code=status.HTTP_204_NO_CONTENT)
async def payments_webhook_handler(payload: dict):
    StripeBillingEventRouter(WEBHOOK_REQUEST_SCOPE, payload).route_event()
    return status.HTTP_204_NO_CONTENT
