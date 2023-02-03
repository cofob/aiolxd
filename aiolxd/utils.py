import urllib.parse as urlparse
from typing import Any, Dict, List, Type, TypeVar, Union, cast
from urllib.parse import urlencode

from .entities.response import BaseResponse

T1 = TypeVar("T1", bound=Union[Dict[str, Any], List[Any]])
T2 = TypeVar("T2", bound=BaseResponse)


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


def ensure_response(
    response: BaseResponse,
    metadata_type: Type[T1],
    response_type: Type[T2],
) -> T2:
    """Ensure that a response is of the correct type."""
    if not isinstance(response, response_type):
        raise RuntimeError(f"Invalid response: response_type={response_type}, response={response}")
    if not isinstance(response.metadata, metadata_type):
        raise RuntimeError(f"Invalid response: metadata_type={metadata_type}, response={response}")
    response.metadata = cast(T1, response.metadata)
    return response
