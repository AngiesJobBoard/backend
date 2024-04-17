from openai import OpenAI
from ajb.config.settings import SETTINGS

from .mock import MockOpenAI
from ..vendor_client_factory import VendorClientFactory


class OpenAIClientFactory(VendorClientFactory[OpenAI]):
    @staticmethod
    def _return_mock(return_content: str = '"content"'):
        return MockOpenAI(return_content)

    @staticmethod
    def _return_client():
        client = OpenAI(
            api_key=SETTINGS.OPENAI_API_KEY,
        )
        return client
