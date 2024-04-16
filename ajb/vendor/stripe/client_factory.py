from stripe import StripeClient
from ajb.config.settings import SETTINGS

from ..vendor_client_factory import VendorClientFactory


class StripeClientFactory(VendorClientFactory):
    @staticmethod
    def _return_mock():
        return None

    @staticmethod
    def _return_client():
        return StripeClient(SETTINGS.STRIPE_API_KEY)
