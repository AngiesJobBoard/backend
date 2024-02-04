from .client import ClerkClient
from .mock import MockClerkClient
from ..vendor_client_factory import VendorClientFactory


class ClerkClientFactory(VendorClientFactory):
    @staticmethod
    def _return_mock():
        return MockClerkClient()

    @staticmethod
    def _return_client():
        return ClerkClient()
