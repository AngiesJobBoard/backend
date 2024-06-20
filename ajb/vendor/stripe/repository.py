"""
The purpose of this integration is to have a manual at first then automated
way to take a company's usage data and create a Stripe invoice for that usage data.

"""

from stripe import StripeClient

from ajb.vendor.stripe.client_factory import StripeClientFactory
from ajb.vendor.stripe.models import StripeCheckoutSessionCreated, Subscription
from ajb.config.settings import SETTINGS


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
        charge_is_recurring: bool = True,
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
            "mode": "subscription" if charge_is_recurring else "payment",
            "success_url": f"{SETTINGS.APP_URL}/subscription?status=confirm",
            "client_reference_id": company_id,
        }
        results = self.client.checkout.sessions.create(params=params)  # type: ignore
        return StripeCheckoutSessionCreated(**results)

    def cancel_subscription(self, subscription_id: str):
        return self.client.subscriptions.cancel(subscription_id)

    def get_original_subscription_item_id(self, subscription_id: str):
        subscription_items = self.client.subscription_items.list({"subscription": subscription_id})  # type: ignore
        return subscription_items.data[0].id

    def update_subscription(self, subscription_id: str, new_price_id: str):
        params = {
            "items": [
                {"price": new_price_id, "quantity": 1},
                {
                    "id": self.get_original_subscription_item_id(subscription_id),
                    "deleted": "true",
                    "quantity": 1,
                },
            ],
            "proration_behavior": "always_invoice",
            "billing_cycle_anchor": "now",
        }
        results = self.client.subscriptions.update(subscription_id, params=params)  # type: ignore
        return Subscription(**results)
