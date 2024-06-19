from pydantic import BaseModel


class CommonMetadata(BaseModel):
    company_id: str


class StripeCheckoutSessionCreated(BaseModel):
    id: str
    amount_subtotal: int
    amount_total: int
    created: int
    customer: str
    expires_at: int
    metadata: CommonMetadata
    url: str


class StripeCheckoutSessionCompleted(BaseModel):
    """
    This is the data model that will be stored on the subscription object
    When the user complete's their payment. We will have this data POSTED to us
    from stripe whenever this event occurs. It will confirm and activate the company's subscription.
    """

    id: str
    object: str  # Should always be checkout.session
    amount_subtotal: int
    amount_total: int
    created: int
    currency: str
    customer: str  # customer id
    invoice: (
        str | None
    )  # only None if the payment occurs only once, subscription ALWAYS have invoice
    livemode: bool  # indicates testing or not
    metadata: CommonMetadata
    payment_status: str  # Looking for status 'paid'
    status: str  # Looking for status 'complete'
    subscription: (
        str | None
    )  # This is the generated subscription id - only occurs with recurring payments
    success_url: str  # The url the user was sent to


class InvoicePaymentSucceeded(BaseModel):
    id: str
    created: int
    effective_at: int
    amount_due: int
    amount_paid: int
    customer: str
    customer_email: str
    customer_name: str
    hosted_invoice_url: str
    livemode: bool
    paid: bool
    status: str
    billing_reason: str  # Currently expect 'subscription_create', 'subscription_cycle', or 'subscription_update', 
    subscription: str  # This is the generated subscription id


class InvoicePaymentFailed(BaseModel):
    """Not currently used..."""
    id: str
    created: int
    customer: str
    customer_email: str
    customer_name: str
    hosted_invoice_url: str
    livemode: bool
    paid: bool
    status: str
    subscription: str  # This is the generated subscription id


class ChargeSuccessful(BaseModel):
    """
    This is used exclusively for AppSumo single payments.
    We also recieve and event when a subscription is updated but we ignore that because we only want to process the invoice payment successful event.
    """
    id: str
    created: int
    amount: int
    amount_captured: int
    customer: str
    paid: bool
    receipt_url: str
    status: str
    description: str  # Currently only looking for 'Subscription update'


class Subscription(BaseModel):
    id: str
    created: int
    customer: str
    latest_invoice: str
    livemode: bool
    status: str
