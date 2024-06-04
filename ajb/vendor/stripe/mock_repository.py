from pydantic import BaseModel


class MockStripeCustomer(BaseModel):
    id: str


class MockStripeRepository:
    def create_customer(self, name: str, email: str, company_id: str):
        return MockStripeCustomer(id="1")  # type: ignore

    def create_invoice(self, *args, **kwargs):
        return "1"
