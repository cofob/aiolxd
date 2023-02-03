from typing import Any, Optional

from pydantic import BaseModel
from pydantic.error_wrappers import ValidationError

from aiolxd.exceptions import AioLXDValidationError
from aiolxd.transport import AbstractTransport


class LazyEntity(BaseModel):
    def __init__(
        self, transport: AbstractTransport, operation: Optional[str] = None, data: Optional[dict[str, Any]] = None
    ) -> None:
        self._transport = transport
        self._operation = operation
        self._is_fetched = False

        if data is not None:
            self.fill(data)

    @property
    def operation(self) -> Optional[str]:
        return self._operation

    @property
    def is_fetched(self) -> bool:
        return self._is_fetched

    def fill(self, data: dict[str, Any]) -> None:
        """Fill the object with the given data.

        This is used when recursion is enabled.
        """
        try:
            super().__init__(**data)
            self._is_fetched = True
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
        if not self._is_fetched:
            await self.update()

    def __repr__(self) -> str:
        return self.__class__.__name__ + f"({self if self._is_fetched else ('Unfetched ' + str(self._operation))})"

    def __setattr__(self, name: str, value: Any) -> None:
        # if name starts with _, set it directly
        # this is used to set the _transport and _operation attributes
        if name.startswith("_"):
            return object.__setattr__(self, name, value)
        return super().__setattr__(name, value)
