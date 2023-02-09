import json
import logging
import ssl
from abc import ABC, abstractmethod
from asyncio import Task, create_task
from enum import Enum
from typing import Any, Coroutine, Dict, Optional, Tuple, TypeVar

import aiohttp

from .entities.response import (
    AsyncResponse,
    BaseResponse,
    ErrorResponse,
    StatusCode,
    SyncResponse,
)
from .exceptions import AioLXDResponseError, AioLXDResponseTypeError
from .utils import update_query_params

logger = logging.getLogger(__name__)

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

    ws_task: Optional[Task[Any]] = None

    @abstractmethod
    async def request(
        self,
        method: RequestMethod,
        path: str,
        data: Optional[Dict[str, Any]] = None,
        *,
        recursion: Optional[bool] = None,
        filter: Optional[str] = None,
    ) -> BaseResponse:
        """Make a request to the LXD API.

        Args:
            method: The HTTP method to use.
            path: The path to the resource.
            data: The data to send with the request.
            recursion: Whether to recurse into sub-resources.
            filter: A filter to apply to the response. String at the moment, but
                    will be changed to a proper filter object in the future.
        """
        pass

    @abstractmethod
    async def websocket(self) -> None:
        """Start a websocket connection to LXD events enspoint."""
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
                ret = AsyncResponse(**args, transport=self)
            else:
                ret = SyncResponse(**args)
        elif response["type"] == "error":
            args["error"] = response["error"]
            args["error_code"] = StatusCode(response["error_code"])
            ret = ErrorResponse(**args)
            raise AioLXDResponseTypeError(ret)

        if ret is None:
            raise ValueError(f"Invalid response type: {response['type']}")

        return ret

    def _process_ws_response(self, response: Dict[str, Any]) -> None:
        logger.debug("Received websocket event: %s", response)

    async def spawn_ws(self) -> None:
        """Start websocket event loop asynchronously."""
        if self.ws_task is not None:
            raise RuntimeError("Websocket task already running")
        self.ws_task = create_task(self.websocket())

    async def close_ws(self) -> None:
        """Close websocket event loop asynchronously."""
        if self.ws_task is not None:
            self.ws_task.cancel()

    async def close(self) -> None:
        """Close the transport."""
        await self.close_ws()

    async def __aenter__(self: T) -> T:
        """Async context manager entry point."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit point."""
        await self.close()

    def __getattr__(self, name: str) -> TransportProxyCaller:
        """Return a proxy caller for the given path."""
        return TransportProxyCaller("/1.0/" + name, self)


class AsyncTransport(AbstractTransport):
    def __init__(
        self,
        url: str,
        session: Optional[aiohttp.ClientSession] = None,
        cert: Optional[Tuple[str, str]] = None,
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
        filter: Optional[str] = None,
    ) -> BaseResponse:
        # Prepare request
        args = {}
        if data is not None and method.value in ("POST", "PUT", "PATCH"):
            args["json"] = data

        # Update URL with query parameters
        url = f"{self._url}{path}"
        if any((recursion is not None, filter is not None)):
            params = {}
            if recursion is not None:
                params["recursion"] = "1" if recursion else "0"
            if filter is not None:
                params["filter"] = filter
            url = update_query_params(url, params)

        logger.debug("Making %s request to %s", method.value, url)

        # Make request
        response = await self._session.request(method.value, url, **self._kwargs, **args)

        logger.debug("Received response from %s: %s", url, response.status)

        if response.status >= 500:
            raise AioLXDResponseError(response, detail=f"Server error: {response.status} {response.reason}")

        # Process response
        try:
            obj = await response.json()
            logger.debug("Response from %s: %s", url, obj)
        except aiohttp.ContentTypeError:
            raise AioLXDResponseError(
                response, detail=f"Response is not JSON: {response.content_type} while expecting application/json"
            )
        except aiohttp.ClientError:
            raise AioLXDResponseError(response)
        except json.JSONDecodeError as e:
            raise AioLXDResponseError(response, detail=f"Response is not JSON: Failed to decode JSON: {e}")

        return self._process_response(obj)

    async def websocket(self) -> None:
        while True:
            # Awful nesting, but it's the only way to get the exception handling right
            try:
                async with self._session.ws_connect(self._url + "/1.0/events") as ws:
                    async for msg in ws:
                        try:
                            data = json.loads(msg.data)
                            self._process_ws_response(data)
                        except json.JSONDecodeError as e:
                            logger.error(f"Failed to decode JSON: {e}")
                            continue
            except Exception as e:
                logger.error(f"Exception occured in events websocket: {e}, restarting...")

    async def close(self) -> None:
        await super().close()
        if self._session_owner:
            await self._session.close()
