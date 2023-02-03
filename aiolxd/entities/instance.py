from typing import Any, Optional

from pydantic import BaseModel
from pydantic.error_wrappers import ValidationError

from aiolxd.exceptions import AioLXDValidationError
from aiolxd.transport import AbstractTransport


class InstanceSchema(BaseModel):
    architecture: str


class InstanceEntity:
    def __init__(
        self, transport: AbstractTransport, operation: Optional[str] = None, object: Optional[dict[str, Any]] = None
    ) -> None:
        self._transport = transport
        self._operation = operation

        self._object: Optional[BaseModel] = None
        if object is not None:
            self.fill(object)

    @property
    def operation(self) -> Optional[str]:
        return self._operation

    @property
    def object(self) -> Optional[BaseModel]:
        return self._object

    @object.setter
    def object(self, object: BaseModel) -> None:
        self._object = object

    @property
    def is_fetched(self) -> bool:
        return self._object is not None

    def fill(self, object: dict[str, Any]) -> None:
        """Fill the object with the given data.

        This is used when recursion is enabled.
        """
        try:
            self._object = InstanceSchema(**object)
        except ValidationError as err:
            raise AioLXDValidationError(err)

    async def update(self) -> None:
        """Update the object from the server."""
        if not self._operation:
            raise RuntimeError("Operation not set")
        resp = await self._transport.get(self._operation)
        if not isinstance(resp.metadata, dict):
            raise RuntimeError("Invalid response")
        self.fill(resp.metadata)

    async def fetch(self) -> None:
        """Fetch the object if it hasn't been fetched yet."""
        if self._object is None:
            await self.update()

    async def __call__(self) -> "InstanceEntity":
        """Fetch the object if it hasn't been fetched yet and return self."""
        await self.fetch()
        return self

    def __getattr__(self, name: str) -> Any:
        if self._object is None:
            raise RuntimeError("Object not fetched")
        return getattr(self._object, name)

    def __repr__(self) -> str:
        return (
            self.__class__.__name__
            + f"({self._object if self._object is not None else ('Unfetched ' + str(self._operation))})"
        )
