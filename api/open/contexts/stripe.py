from fastapi import APIRouter, Request, status, Depends

from ajb.base import RequestScope
from ajb.contexts.billing.usecase.complete_create_subscription import (
    CompleteCreateSubscription,
    StripeCheckoutSessionCompleted,
)
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
    """
    Currently handles:
      - checkout.session.completed

    Needs to also handle:
      - invoice.payment_succeeded
      - invoice.payment_failed

    """
    if "object" in payload:
        payload = payload["object"]
    CompleteCreateSubscription(WEBHOOK_REQUEST_SCOPE).complete_subscription_setup(
        data=StripeCheckoutSessionCompleted(**payload)
    )
    return status.HTTP_204_NO_CONTENT
