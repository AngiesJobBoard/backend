from sendgrid import SendGridAPIClient
from ajb.config.settings import SETTINGS

from .mock import MockSendgrid
from ..vendor_client_factory import VendorClientFactory


class SendgridFactory(VendorClientFactory[SendGridAPIClient]):
    @staticmethod
    def _return_mock():
        return MockSendgrid()

    @staticmethod
    def _return_client():
        return SendGridAPIClient(SETTINGS.SENDGRID_API_KEY)
