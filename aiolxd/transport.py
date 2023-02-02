import json
import ssl
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Callable, Coroutine, Dict, Optional, TypeVar

import aiohttp

from .entities.response import (
    AsyncResponse,
    BaseResponse,
    ErrorResponse,
    StatusCode,
    SyncResponse,
)
from .exceptions import AioLXDResponseError
from .utils import update_query_params

T = TypeVar("T", bound="AbstractTransport")


class RequestMethod(Enum):
    """HTTP request methods."""

    GET = "GET"
    POST = "POST"
    HEAD = "HEAD"
    PUT = "PUT"
    DELETE = "DELETE"
    OPTIONS = "OPTIONS"
    PATCH = "PATCH"


class TransportProxyCaller:
    def __init__(self, path: str, parent: "AbstractTransport") -> None:
        self.path = path
        self.parent = parent

    def slash(self, name: str) -> "TransportProxyCaller":
        return TransportProxyCaller(f"{self.path}/{name}", self.parent)

    def __getattr__(self, name: str) -> "TransportProxyCaller":
        return self.slash(name)

    def __call__(self, **kwargs: Any) -> Coroutine[Any, Any, BaseResponse]:
        return self.parent.request(RequestMethod.GET, self.path, **kwargs)

    def get(self, **kwargs: Any) -> Coroutine[Any, Any, BaseResponse]:
        return self.parent.request(RequestMethod.GET, self.path, **kwargs)

    def post(self, **kwargs: Any) -> Coroutine[Any, Any, BaseResponse]:
        return self.parent.request(RequestMethod.POST, self.path, **kwargs)

    def put(self, **kwargs: Any) -> Coroutine[Any, Any, BaseResponse]:
        return self.parent.request(RequestMethod.PUT, self.path, **kwargs)

    def delete(self, **kwargs: Any) -> Coroutine[Any, Any, BaseResponse]:
        return self.parent.request(RequestMethod.DELETE, self.path, **kwargs)

    def options(self, **kwargs: Any) -> Coroutine[Any, Any, BaseResponse]:
        return self.parent.request(RequestMethod.OPTIONS, self.path, **kwargs)

    def patch(self, **kwargs: Any) -> Coroutine[Any, Any, BaseResponse]:
        return self.parent.request(RequestMethod.PATCH, self.path, **kwargs)

    def head(self, **kwargs: Any) -> Coroutine[Any, Any, BaseResponse]:
        return self.parent.request(RequestMethod.HEAD, self.path, **kwargs)


class AbstractTransport(ABC):
    """Abstract transport class.

    This class is used to make requests to the LXD API.
    """

    @abstractmethod
    async def request(
        self,
        method: RequestMethod,
        path: str,
        data: Optional[Dict[str, Any]] = None,
        *,
        recursion: Optional[bool] = None,
    ) -> BaseResponse:
        """Make a request to the LXD API."""
        pass

    def get(self, path: str, **kwargs: Any) -> Coroutine[Any, Any, BaseResponse]:
        """Make a GET request to the LXD API."""
        return self.request(RequestMethod.GET, path, **kwargs)

    def post(self, path: str, **kwargs: Any) -> Coroutine[Any, Any, BaseResponse]:
        """Make a POST request to the LXD API."""
        return self.request(RequestMethod.POST, path, **kwargs)

    def put(self, path: str, **kwargs: Any) -> Coroutine[Any, Any, BaseResponse]:
        """Make a PUT request to the LXD API."""
        return self.request(RequestMethod.PUT, path, **kwargs)

    def delete(self, path: str, **kwargs: Any) -> Coroutine[Any, Any, BaseResponse]:
        """Make a DELETE request to the LXD API."""
        return self.request(RequestMethod.DELETE, path, **kwargs)

    def patch(self, path: str, **kwargs: Any) -> Coroutine[Any, Any, BaseResponse]:
        """Make a PATCH request to the LXD API."""
        return self.request(RequestMethod.PATCH, path, **kwargs)

    def head(self, path: str, **kwargs: Any) -> Coroutine[Any, Any, BaseResponse]:
        """Make a HEAD request to the LXD API."""
        return self.request(RequestMethod.HEAD, path, **kwargs)

    def options(self, path: str, **kwargs: Any) -> Coroutine[Any, Any, BaseResponse]:
        """Make a OPTIONS request to the LXD API."""
        return self.request(RequestMethod.OPTIONS, path, **kwargs)

    def _process_response(self, response: Dict[str, Any]) -> BaseResponse:
        """Process a response from the LXD API."""
        if "type" not in response:
            raise ValueError("Response has no type")

        args: Dict[str, Any] = {
            "type_": response["type"],
            "metadata": response["metadata"],
        }

        ret: Optional[BaseResponse] = None

        if response["type"] == "sync" or response["type"] == "async":
            args["status"] = response["status"]
            args["status_code"] = StatusCode(response["status_code"])
            if response["type"] == "async":
                args["operation"] = response["operation"]
                ret = AsyncResponse(**args)
            else:
                ret = SyncResponse(**args)
        elif response["type"] == "error":
            args["error"] = response["error"]
            args["error_code"] = StatusCode(response["error_code"])
            ret = ErrorResponse(**args)

        if ret is None:
            raise ValueError(f"Invalid response type: {response['type']}")

        return ret

    async def close(self) -> None:
        """Close the transport."""
        pass

    async def __aenter__(self: T) -> T:
        """Async context manager entry point."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit point."""
        await self.close()

    def __getattr__(self, name: str) -> TransportProxyCaller:
        """Return a proxy caller for the given path."""
        return TransportProxyCaller(name, self)


class AsyncTransport(AbstractTransport):
    def __init__(
        self,
        url: str,
        session: Optional[aiohttp.ClientSession] = None,
        cert: Optional[tuple[str, str]] = None,
        verify: Optional[bool] = None,
        **kwargs: Any,
    ) -> None:
        self._url = url
        self._kwargs = kwargs

        session_args = {}
        if cert is not None:
            ssl_context = ssl.SSLContext()
            ssl_context.load_cert_chain(*cert)
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            session_args["connector"] = connector

        self._session = session or aiohttp.ClientSession(**session_args)  # type: ignore
        self._session_owner = session is None
        if verify is not None:
            self._session.verify_ssl = verify
        if cert is not None:
            self._session.cert = cert

    async def request(
        self,
        method: RequestMethod,
        path: str,
        data: Optional[Dict[str, Any]] = None,
        *,
        recursion: Optional[bool] = None,
    ) -> BaseResponse:
        # Prepare request
        args = {}
        if data is not None and method.value in ("POST", "PUT", "PATCH"):
            args["json"] = data

        # Update URL with query parameters
        url = f"{self._url}/{path}"
        if any((recursion is not None,)):
            params = {}
            if recursion is not None:
                params["recursion"] = "1" if recursion else "0"
            url = update_query_params(url, params)

        print(url)

        # Make request
        response = await self._session.request(method.value, url, **self._kwargs, **args)

        if response.status >= 500:
            raise AioLXDResponseError(response, detail=f"Server error: {response.status} {response.reason}")

        # Process response
        try:
            obj = await response.json()
        except aiohttp.ContentTypeError:
            raise AioLXDResponseError(
                response, detail=f"Response is not JSON: {response.content_type} while expecting application/json"
            )
        except aiohttp.ClientError as e:
            raise AioLXDResponseError(response)
        except json.JSONDecodeError as e:
            raise AioLXDResponseError(response, detail=f"Response is not JSON: Failed to decode JSON: {e}")

        return self._process_response(obj)

    async def close(self) -> None:
        if self._session_owner:
            await self._session.close()
