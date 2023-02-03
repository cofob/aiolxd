from typing import Any, Generic, Optional, Type, TypeVar

from pydantic import BaseModel
from pydantic.error_wrappers import ValidationError

from aiolxd.exceptions import AioLXDValidationError
from aiolxd.transport import AbstractTransport

# БОЛЬШЕ ДЖЕНЕРИКОВ БОГУ ДЖЕНЕРИКОВ
S = TypeVar("S", bound=BaseModel)
T = TypeVar("T", bound="LazyEntity[BaseModel]")


# Я СКАЗАЛ БОЛЬШЕ!
class LazyEntity(Generic[S]):
    schema: Type[S]

    def __init__(
        self, transport: AbstractTransport, operation: Optional[str] = None, data: Optional[dict[str, Any]] = None
    ) -> None:
        self._transport = transport
        self._operation = operation

        self._data: Optional[S] = None
        if data is not None:
            self.fill(data)

    @property
    def operation(self) -> Optional[str]:
        return self._operation

    @property
    def data(self) -> Optional[S]:
        return self._data

    @data.setter
    def data(self, data: S) -> None:
        self._data = data

    @property
    def is_fetched(self) -> bool:
        return self._data is not None

    def fill(self, object: dict[str, Any]) -> None:
        """Fill the object with the given data.

        This is used when recursion is enabled.
        """
        try:
            self._data = self.schema(**object)
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
        if self._data is None:
            await self.update()

    def __getattr__(self, name: str) -> Any:
        if self._data is None:
            raise RuntimeError("Object not fetched")
        return getattr(self._data, name)

    def __repr__(self) -> str:
        return (
            self.__class__.__name__
            + f"({self._data if self._data is not None else ('Unfetched ' + str(self._operation))})"
        )


# Это работает, но mypy активно воспротивляется это принимать. Он думает
# что тип объекта не меняется и остаётся как pydantic.BaseModeL, поэтому
# методы типа __init__, fetch и прочие - не воспринимаются им как валидные
# при этом Pylance считывает это корректно.
def lazy_entity(cls: Type[S]) -> Type[LazyEntity[S]]:
    """Create a lazy entity from a pydantic model.

    Example:
        >>> from pydantic import BaseModel
        >>> from aiolxd.entities.abc import lazy_entity
        >>>
        >>> @lazy_entity
        >>> class MyEntity(BaseModel):
        ...     foo: str
        ...     bar: int
        >>>
        >>> e = MyEntity(transport, operation="/1.0/operations/1234")
        >>> e
        "MyEntity(Unfetched /1.0/operations/1234)"
        >>> await e.fetch()
        >>> e
        "MyEntity(foo='bar', bar=123)"
        >>> MyEntity(transport, data={"foo": "bar", "bar": 123})
        "MyEntity(foo='bar', bar=123)"
    """

    class LazyEntityWrapper(LazyEntity[S]):
        schema = cls

    LazyEntityWrapper.__name__ = cls.__name__

    return LazyEntityWrapper
