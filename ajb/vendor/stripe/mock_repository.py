from pydantic import BaseModel
from ajb.vendor.stripe.repository import StripeRepository


class MockStripeCustomer(BaseModel):
    id: str


class MockStripeRepository(StripeRepository):
    def __init__(self, *args, **kwargs):
        pass

    def create_customer(self, name: str, email: str, company_id: str):
        return MockStripeCustomer(id="1")  # type: ignore

    def create_invoice(self, *args, **kwargs):
        return "1"
