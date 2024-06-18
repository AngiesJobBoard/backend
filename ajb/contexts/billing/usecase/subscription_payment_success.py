from ajb.base import BaseUseCase
from ajb.vendor.stripe.models import InvoicePaymentSucceeded


class SubscriptionPaymentSuccess(BaseUseCase):
    def update_company_usage(self, data: InvoicePaymentSucceeded): ...
