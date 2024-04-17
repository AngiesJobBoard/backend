"""
The purpose of this integration is to have a manual at first then automated way to take a company's usage data and create a Stripe invoice for that usage data.

"""

import typing as t
from stripe import StripeClient

from ajb.vendor.stripe.client_factory import StripeClientFactory
from ajb.utils import generate_random_short_code


from pydantic import BaseModel


def generate_invoice_number(customer_id: str, billing_period: str):
    return f"{customer_id}-{billing_period}-{generate_random_short_code()}"[0:26]


class InvoiceLineItem(BaseModel):
    description: str
    unit_amount_decimal: str
    quantity: int


class CreateInvoiceData(BaseModel):
    stripe_customer_id: str
    description: str
    invoice_number: str
    invoice_items: list[InvoiceLineItem]


class DefaultInvoiceSettings:
    CURRENCY = "usd"
    DAYS_UNTIL_DUE = 30
    COLLECTION_METHOD: t.Literal["charge_automatically", "send_invoice"] = (
        "send_invoice"
    )


class StripeRepository:
    def __init__(self, client: StripeClient | None = None):
        self.client = client or StripeClientFactory.get_client()

    def create_customer(self, name: str, email: str, company_id: str):
        params = {
            "name": name,
            "email": email,
            "metadata": {"company_id": company_id},
        }
        return self.client.customers.create(params=params)  # type: ignore

    def create_invoice(self, invoice_data: CreateInvoiceData):
        draft_invoice = self.client.invoices.create(
            params={
                "currency": DefaultInvoiceSettings.CURRENCY,
                "days_until_due": DefaultInvoiceSettings.DAYS_UNTIL_DUE,
                "customer": invoice_data.stripe_customer_id,
                "description": invoice_data.description,
                "number": invoice_data.invoice_number,
                "collection_method": DefaultInvoiceSettings.COLLECTION_METHOD,
            }
        )
        for item in invoice_data.invoice_items:
            self.client.invoice_items.create(
                params={
                    "invoice": draft_invoice.id,  # type: ignore
                    "currency": DefaultInvoiceSettings.CURRENCY,
                    "description": item.description,
                    "unit_amount_decimal": item.unit_amount_decimal,
                    "quantity": item.quantity,
                    "customer": invoice_data.stripe_customer_id,
                }
            )

        return self.client.invoices.retrieve(draft_invoice.id)  # type: ignore


stripe = StripeRepository()

new_invoice = stripe.create_invoice(
    CreateInvoiceData(
        stripe_customer_id="cus_PwFv8YLq3dGui0",
        description="AJB Monthly usage invoice",
        invoice_number=generate_invoice_number("abc123", "2022-01"),
        invoice_items=[
            InvoiceLineItem(
                description="Pro Subscription",
                unit_amount_decimal="10000",
                quantity=1,
            ),
            InvoiceLineItem(
                description="Additional Pro Resume scans",
                unit_amount_decimal="10",
                quantity=15,
            ),
            InvoiceLineItem(
                description="Additional Pro Match scores",
                unit_amount_decimal="10",
                quantity=150,
            ),
            InvoiceLineItem(
                description="Additional Pro Questions answered",
                unit_amount_decimal="10",
                quantity=323,
            ),
        ]
    )
)
