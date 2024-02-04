import typing
import urllib.parse as urlparse
from urllib.parse import urlencode


def modify_query_parameters_in_url(url: str, new_params: dict[str, typing.Any]) -> str:
    parsed = list(urlparse.urlparse(url))
    query = dict(urlparse.parse_qsl(parsed[4]))
    query.update(new_params)
    parsed[4] = urlencode(query)
    return urlparse.urlunparse(parsed)
