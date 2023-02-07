from typing import Any, List, Type, TypeVar

from .api.abc import ApiEndpointGroup
from .api.instance import InstanceGroup
from .entities.response import SyncResponse
from .entities.status import StatusEntity
from .exceptions import AioLXDUntrustedCredentials
from .transport import AbstractTransport, AsyncTransport
from .utils import ensure_response

T = TypeVar("T", bound="LXD")
T_API = TypeVar("T_API", bound="ApiEndpointGroup")


class LXD:
    """LXD client.

    This is the main entry point for the LXD client. It provides access to
    all the LXD API endpoints. It also provides a context manager to
    automatically close the connection when done.

    Example:
    >>> async with LXD("https://localhost:8443") as lxd:
    ...     print(await lxd.instances())
    """

    transport: AbstractTransport
    api_extensions: List[str]

    def __init__(self, transport: AbstractTransport) -> None:
        """LXD client.

        This is the main entry point for the LXD client. It provides access to
        all the LXD API endpoints. It also provides a context manager to
        automatically close the connection when done.

        Example:
        >>> async with LXD("https://localhost:8443") as lxd:
        ...     print(await lxd.instances())
        """

        self.transport = transport
        self.api_extensions = []

        self.instance = self._init_api_group(InstanceGroup)

    @classmethod
    def with_async(ctx: Type[T], *args: Any, **kwargs: Any) -> T:
        """Create a new instance of this class with an async transport."""
        return ctx(AsyncTransport(*args, **kwargs))

    def _init_api_group(self, class_: Type[T_API], **kwargs: Any) -> T_API:
        """Initialize an API endpoint group."""
        return class_(self.transport, self.api_extensions, **kwargs)

    async def start(self) -> None:
        """Start the LXD client.

        This run connection checks and other setup.
        """
        await self.transport.spawn_ws()
        resp = await self.transport.get("/1.0")
        ensure_response(resp, dict, SyncResponse)
        if not isinstance(resp.metadata, dict):
            raise RuntimeError("Invalid response")
        status = StatusEntity(**resp.metadata)
        self.api_extensions = status.api_extensions
        if status.auth != "trusted":
            raise AioLXDUntrustedCredentials()

    async def __aenter__(self: T) -> T:
        """Async context manager entry point."""
        await self.start()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit point."""
        await self.transport.close()

    def __enter__(self: T) -> T:
        """Context manager entry point."""
        raise RuntimeError("Use async context manager instead")
