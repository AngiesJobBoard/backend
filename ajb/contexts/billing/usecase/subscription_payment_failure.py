"""
Update subscription to say payment is late
send out emails etc.
"""

from ajb.base import BaseUseCase
from ajb.vendor.stripe.models import InvoicePaymentFailed


class SubscriptionPaymentFailure(BaseUseCase):
    def update_company_usage(self, data: InvoicePaymentFailed): ...
