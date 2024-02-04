from twilio.rest import Client

from ajb.config.settings import SETTINGS

from .mock import MockTwilio
from ..vendor_client_factory import VendorClientFactory


class TwilioFactory(VendorClientFactory):
    @staticmethod
    def _return_mock():
        return MockTwilio()

    @staticmethod
    def _return_client():
        return Client(SETTINGS.TWILIO_ACCOUNT_SID, SETTINGS.TWILIO_AUTH_TOKEN)
