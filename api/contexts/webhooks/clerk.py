from fastapi import APIRouter, Request, status, Depends

from ajb.base import RequestScope
from ajb.contexts.webhooks.ingress.users.usecase import WebhookUserUseCase
from ajb.vendor.clerk.models import (
    ClerkUserWebhookEvent,
)

from api.vendors import db


WEBHOOK_REQUEST_SCOPE = RequestScope(user_id="clerk_webhook", db=db, company_id=None)


async def verify_clerk_webhook_event(request: Request) -> dict:
    return await request.json()


router = APIRouter(
    tags=["Webhooks"],
    prefix="/webhooks/clerk",
    dependencies=[Depends(verify_clerk_webhook_event)],
)


@router.post("/users", status_code=status.HTTP_204_NO_CONTENT)
async def users_webhook_handler(payload: dict):
    return WebhookUserUseCase(WEBHOOK_REQUEST_SCOPE).handle_webhook_event(
        ClerkUserWebhookEvent(**payload)
    )
