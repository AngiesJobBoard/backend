from groq import Groq
from ajb.config.settings import SETTINGS

from .mock import MockGroq
from ..vendor_client_factory import VendorClientFactory


class GroqClientFactory(VendorClientFactory[Groq]):
    @staticmethod
    def _return_mock(return_content: str = '"content"'):
        return MockGroq(return_content)

    @staticmethod
    def _return_client():
        client = Groq(
            api_key=SETTINGS.GROQ_API_KEY,
        )
        return client
