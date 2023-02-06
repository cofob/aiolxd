from abc import ABC
from typing import Any, List

from ..transport import AbstractTransport


class ApiEndpointGroup(ABC):
    """Base class for API endpoint groups.

    Example:
    >>> class InstanceGroup(ApiEndpointGroup):
    ...     async def list(self, recursion: bool = False) -> List[InstanceEntity]:
    ...         resp = self.transport.instances(recursion=recursion)
    ...         ...
    ...
    ...     async def get(self, name: str) -> InstanceEntity:
    ...         resp = self.transport.instance(name)
    ...         ...
    ...
    ...     async def create(self, instance: InstanceEntity) -> InstanceEntity:
    ...         resp = self.transport.instances.post(instance.dict())
    ...         ...
    ...
    >>> instance = InstanceGroup(transport)
    """

    def __init__(self, transport: AbstractTransport, api_extensions: List[str], **kwargs: Any) -> None:
        """Initialize the endpoint group."""
        self.transport = transport
        self.api_extensions = api_extensions
        for key, value in kwargs.items():
            setattr(self, key, value)

    def is_supported(self, extension: str) -> bool:
        """Check if an extension is supported."""
        return extension in self.api_extensions
