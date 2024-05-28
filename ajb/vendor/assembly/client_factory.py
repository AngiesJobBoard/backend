import assemblyai as aai

from ajb.config.settings import SETTINGS

from ..vendor_client_factory import VendorClientFactory


class AssemblyAIClientFactory(VendorClientFactory[aai.Client]):

    @staticmethod
    def _return_client():
        client = aai.Client(settings=aai.Settings(api_key=SETTINGS.ASSEMBLYAI_API_KEY))
        return client
