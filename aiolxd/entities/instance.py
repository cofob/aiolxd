from typing import Any, Optional

from pydantic import BaseModel

from aiolxd.transport import AbstractTransport


class InstanceSchema(BaseModel):
    architecture: str


class InstanceEntity:
    def __init__(self, transport: AbstractTransport, operation: Optional[str] = None):
        self._transport = transport
        self._operation = operation
        self._object: Optional[BaseModel] = None

    def fill(self, object: BaseModel) -> None:
        self._object = object

    async def update(self) -> None:
        if not self._operation:
            raise RuntimeError("Operation not set")
        resp = await self._transport.get(self._operation)
        if not isinstance(resp.metadata, dict):
            raise RuntimeError("Invalid response")
        self._object = InstanceSchema(**resp.metadata)

    async def fetch(self) -> None:
        if self._object is None:
            await self.update()

    def __getattr__(self, name: str) -> Any:
        if self._object is None:
            raise RuntimeError("Object not fetched")
        return getattr(self._object, name)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self._object if self._object is not None else 'Unititialized'})"
