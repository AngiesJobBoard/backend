"""
The purpose of this integration is to have a manual at first then automated way to take a company's usage data and create a Stripe invoice for that usage data.

It is also responsible for creating or updating a subscription for a company.
"""
from stripe import StripeClient

from .client_factory import StripeClientFactory


class StripeRepository:
    def __init__(self, client: StripeClient | None = None):
        self.client = client or StripeClientFactory.get_client()

    def create_customer(self):...

    def create_subscription(self):...

    def update_subscription(self):...

    def delete_subscription(self):...

    def create_invoice(self):...

    def update_invoice(self):...



stripe = StripeRepository()

client = stripe.client

created_stripe_customer = client.customers.create(
    params={
        "name": "Test Stripe Customer",
        "email": "email@address.com",
    }
)

