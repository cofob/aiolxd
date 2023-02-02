import urllib.parse as urlparse
from typing import Dict
from urllib.parse import urlencode


def update_query_params(url: str, params: Dict[str, str]) -> str:
    """Update the query parameters of a URL.

    Example:
        >>> update_query_params("https://example.com", {"foo": "bar"})
        'https://example.com?foo=bar'
        >>> update_query_params("https://example.com?foo=bar", {"foo": "baz"})
        'https://example.com?foo=baz'
        >>> update_query_params("https://example.com?foo=bar", {"bar": "baz"})
        'https://example.com?foo=bar&bar=baz'
    """
    parts = urlparse.urlparse(url)
    query = dict(urlparse.parse_qsl(parts.query))
    query.update(params)
    parts = parts._replace(query=urlencode(query))
    return urlparse.urlunparse(parts)
