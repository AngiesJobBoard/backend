from algoliasearch.search_client import SearchClient
from algoliasearch.insights_client import InsightsClient
from ajb.config.settings import SETTINGS

from .mock import MockAlgoliaClient, MockAlgoliaInsightsClient
from ..vendor_client_factory import VendorClientFactory


class AlgoliaClientFactory(VendorClientFactory):
    @staticmethod
    def _return_mock():
        return MockAlgoliaClient()

    @staticmethod
    def _return_client():
        return SearchClient.create(
            app_id=SETTINGS.ALGOLIA_APP_ID, api_key=SETTINGS.ALGOLIA_API_KEY
        )


class AlgoliaInsightsFactory(VendorClientFactory):
    @staticmethod
    def _return_mock():
        return MockAlgoliaInsightsClient()

    @staticmethod
    def _return_client():
        return InsightsClient.create(
            app_id=SETTINGS.ALGOLIA_APP_ID, api_key=SETTINGS.ALGOLIA_API_KEY
        )
