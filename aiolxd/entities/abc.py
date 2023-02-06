from typing import Any, Dict, Optional

from pydantic import BaseModel
from pydantic.error_wrappers import ValidationError

from ..exceptions import AioLXDValidationError
from ..transport import AbstractTransport


class LazyEntity(BaseModel):
    """Base class for entities that are lazily fetched from the server.

    This is used for entities that are returned as an operation string
    instead of the full object.

    Internally, this is a pydantic model that is filled with the data
    from the server when the fetch method is called.

    Example:
        >>> from aiolxd.entities.abc import LazyEntity
        >>>
        >>> class MyEntity(LazyEntity):
        ...     foo: str
        ...
        >>> entity = MyEntity(None, operation="/1.0/operations/123")
        >>> await entity.fetch()
        >>> entity.foo
        'bar'
        >>>
        >>> entity = MyEntity(None, data={"foo": "bar"})
        >>> entity.foo
        'bar'
    """

    def __init__(
        self, transport: AbstractTransport, operation: Optional[str] = None, data: Optional[Dict[str, Any]] = None
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

    def fill(self, data: Dict[str, Any]) -> None:
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
