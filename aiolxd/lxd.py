from abc import ABC
from typing import Any, Type, TypeVar

from .entities.instance import InstanceEntity
from .transport import AbstractTransport, AsyncTransport

T = TypeVar("T", bound="BaseLXD")


class BaseLXD(ABC):
    transport: AbstractTransport

    def __init__(self, transport: AbstractTransport) -> None:
        self.transport = transport


class LXD(BaseLXD):
    @classmethod
    def with_async(ctx: Type[T], *args: Any, **kwargs: Any) -> T:
        """Create a new instance of this class with an async transport."""
        return ctx(AsyncTransport(*args, **kwargs))

    async def instances(self, recursion: bool = False) -> list[InstanceEntity]:
        resp = await self.transport.instances(recursion=recursion)
        if not isinstance(resp.metadata, list):
            raise RuntimeError("Invalid response")
        if recursion:
            return [InstanceEntity(self.transport, data=i) for i in resp.metadata]
        return [InstanceEntity(self.transport, operation) for operation in resp.metadata]

    async def __aenter__(self: T) -> T:
        """Async context manager entry point."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit point."""
        await self.transport.close()
