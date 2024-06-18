"""
The purpose of this integration is to have a manual at first then automated
way to take a company's usage data and create a Stripe invoice for that usage data.

"""

from stripe import StripeClient

from ajb.vendor.stripe.client_factory import StripeClientFactory
from ajb.vendor.stripe.models import StripeCheckoutSessionCreated


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

    def create_subscription_checkout_session(
        self,
        company_id: str,
        stripe_customer_id: str,
        price_id: str,
    ) -> StripeCheckoutSessionCreated:
        params = {
            "customer": stripe_customer_id,
            "metadata": {"company_id": company_id},
            "line_items": [
                {
                    "price": price_id,
                    "quantity": 1,
                }
            ],
            "mode": "subscription",
            "success_url": "http://localhost:3000/subscription-success",
            "client_reference_id": company_id,
        }
        results = self.client.checkout.sessions.create(params=params)  # type: ignore
        return StripeCheckoutSessionCreated(**results)

    def cancel_subscription(self, subscription_id: str):
        return self.client.subscriptions.cancel(subscription_id)
