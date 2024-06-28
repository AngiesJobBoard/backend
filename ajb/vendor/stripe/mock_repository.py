# pylint: disable=super-init-not-called
import time
from unittest.mock import MagicMock
from pydantic import BaseModel
from ajb.vendor.stripe.models import InvoicePaymentSucceeded
from ajb.vendor.stripe.repository import StripeRepository


class MockStripeCustomer(BaseModel):
    id: str


class MockStripeRepository(StripeRepository):
    company_id: str

    def __init__(self, *args, **kwargs):
        self.client = MagicMock()  # Initialize mock stripe client
        self.client.checkout.sessions.create = self.create_session
        self.creation_time = int(round(time.time()))
        self.company_id = "1"

    def create_customer(self, name: str, email: str, company_id: str):
        return MockStripeCustomer(id="1")  # type: ignore

    def create_invoice(self, *args, **kwargs):
        return "1"

    def create_session(self, params: dict | None = None):
        return {
            "id": self.company_id,
            "amount_subtotal": "10",
            "amount_total": "10",
            "created": str(self.creation_time),
            "customer": self.company_id,
            "expires_at": str(self.creation_time + 1000000),
            "metadata": {
                "company_id": "1",
            },
            "url": "test.com",
            "object": "checkout.session",
            "currency": "USD",
            "livemode": False,
            "payment_status": "paid",
            "status": "complete",
            "success_url": "success.test.com",
            "invoice": "1",
            "subscription": "1",
        }

    def create_invoice_payment_suceeded(self):
        return InvoicePaymentSucceeded(
            id=self.company_id,
            created=1622547800,
            effective_at=self.creation_time,
            amount_due=1000,
            amount_paid=1000,
            customer=self.company_id,
            customer_email="rcg@example.com",
            customer_name="recruiting guy",
            hosted_invoice_url="invoices.test.com",
            livemode=False,
            paid=True,
            status="paid",
            billing_reason="subscription_create",
            subscription="sub_1234567890",
        )
