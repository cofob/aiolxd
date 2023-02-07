from typing import List

from ..entities.instance import (
    InstanceCreateRequest,
    InstanceEntity,
    InstanceSource,
)
from ..entities.response import AsyncResponse, SyncResponse
from ..utils import ensure_response
from .abc import ApiEndpointGroup


class InstanceGroup(ApiEndpointGroup):
    """API endpoint group for instances."""

    async def list(self, recursion: bool = False) -> List[InstanceEntity]:
        """List all instances."""
        resp = await self.transport.instances(recursion=recursion)
        resp = ensure_response(resp, list, SyncResponse)
        if not isinstance(resp.metadata, list):
            raise TypeError("Expected list, got {!r}".format(resp.metadata))
        if recursion:
            return [InstanceEntity(self.transport, data=item) for item in resp.metadata]
        return [InstanceEntity(self.transport, operation=item) for item in resp.metadata]

    async def create(
        self,
        *,
        architecture: str = "x86_64",
        name: str,
        source: str,
        source_type: str = "image",
        type_: str = "container",
    ) -> None:
        body = InstanceCreateRequest(
            architecture=architecture,
            name=name,
            source=InstanceSource(alias=source, type=source_type),
            type=type_,
        )
        resp = await self.transport.instances.post(data=body.dict())
        resp = ensure_response(resp, dict, AsyncResponse)
