from unittest import mock
from ajb.vendor.google_maps import get_lat_long_from_address


def test_get_lat_long_from_address():
    with mock.patch("requests.get") as mock_get:
        mock_response = mock.Mock()
        mock_response.json.return_value = {
            "results": [{"geometry": {"location": {"lat": 1, "lng": 2}}}]
        }
        mock_get.return_value = mock_response
        lat, lng = get_lat_long_from_address("somewhere")
        assert lat == 1
        assert lng == 2
