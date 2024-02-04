from ajb.vendor.algolia.repository import AlgoliaSearchRepository
from ajb.vendor.algolia.mock import MockAlgoliaClient
from ajb.vendor.algolia.models import AlgoliaIndex, AlgoliaSearchParams


class TestAlgoliaSearch:
    client = MockAlgoliaClient()
    index = AlgoliaIndex.JOBS
    repo = AlgoliaSearchRepository(index, client)

    def test_search(self):
        search_params = AlgoliaSearchParams(query="python")
        res = self.repo.search(search_params)
        assert res.hits == []

    def test_get_update_delete_search(self):
        self.repo.create_object("1", {"nice": "data"})
        res = self.repo.get("1")
        assert res["nice"] == "data"

        res = self.repo.search(AlgoliaSearchParams(query="doesnt_matter"))
        assert res.hits[0]["nice"] == "data"

        self.repo.update_object("1", {"nice": "data2"})
        res = self.repo.get("1")
        assert res["nice"] == "data2"

        res = self.repo.search(AlgoliaSearchParams(query="doesnt_matter"))
        assert res.hits[0]["nice"] == "data2"
