from typing import List

from ..entities.instance import InstanceEntity
from ..entities.response import SyncResponse
from ..utils import ensure_response
from .abc import ApiEndpointGroup


class InstanceGroup(ApiEndpointGroup):
    """API endpoint group for instances."""

    async def list(self, recursion: bool = False) -> List[InstanceEntity]:
        """List all instances."""
        resp = await self.transport.instances(recursion=recursion)
        resp = ensure_response(resp, list, SyncResponse)
        if not isinstance(resp.metadata, list):
            raise TypeError("Expected list of instances")
        if recursion:
            return [InstanceEntity(self.transport, data=item) for item in resp.metadata]
        return [InstanceEntity(self.transport, operation=item) for item in resp.metadata]
