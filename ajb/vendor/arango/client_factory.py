from arango.client import ArangoClient
from ajb.config.settings import SETTINGS
from ..vendor_client_factory import VendorClientFactory


class ArangoClientFactory(VendorClientFactory[ArangoClient]):
    """
    For Arango we do not provide a mock, it's expected that you
    are running it locally in a docker container. This is the case
    for running in the pipeline as well
    """

    @staticmethod
    def _return_mock():
        return ArangoClient(hosts=SETTINGS.ARANGO_URL)

    @staticmethod
    def _return_client():
        return ArangoClient(hosts=SETTINGS.ARANGO_URL)
