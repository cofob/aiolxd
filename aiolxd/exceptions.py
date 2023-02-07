from typing import Any, Optional

from aiohttp import ClientResponse
from aiohttp.typedefs import CIMultiDictProxy
from pydantic.error_wrappers import ValidationError

from .entities.response import ErrorResponse


class AioLXDException(Exception):
    """Base exception for all AioLXD exceptions."""

    pass


class AioLXDResponseError(AioLXDException):
    """Base exception for all AioLXD response errors."""

    def __init__(self, response: ClientResponse, detail: Optional[str] = None) -> None:
        """Initialize exception."""
        self.response = response
        self.detail = f"Response error: {response.status}" if detail is None else detail
        super().__init__(self.detail)

    def __str__(self) -> str:
        """Return a string representation of the exception."""
        return self.detail

    def __repr__(self) -> str:
        """Return a representation of the exception."""
        return f"{self.__class__.__name__}({self.response!r}, {self.detail!r})"

    @property
    def status(self) -> int:
        """Return response status."""
        return self.response.status

    @property
    def reason(self) -> Optional[str]:
        """Return response reason."""
        return self.response.reason

    @property
    def headers(self) -> CIMultiDictProxy[str]:
        """Return response headers."""
        return self.response.headers

    async def text(self) -> Optional[str]:
        """Return response text."""
        return await self.response.text()

    async def json(self) -> Optional[Any]:
        """Return response json."""
        return await self.response.json()


class AioLXDValidationError(AioLXDException):
    """Exception for AioLXD response validation errors."""

    def __init__(self, error: ValidationError, detail: Optional[str] = None) -> None:
        """Initialize exception."""
        self.error = error
        self.detail = f"Validation error: {error.errors()}" if detail is None else detail
        super().__init__(self.detail)


class AioLXDResponseInvalidCode(AioLXDResponseError):
    """Exception for AioLXD invalid response codes."""

    def __init__(self, response: ClientResponse, detail: Optional[str] = None) -> None:
        """Initialize exception."""
        self.detail = f"Invalid response code: {response.status}" if detail is None else detail
        super().__init__(response, self.detail)


class AioLXDResponseNotFound(AioLXDResponseError):
    """Exception for AioLXD not found errors."""

    def __init__(self, response: ClientResponse, detail: Optional[str] = None) -> None:
        """Initialize exception."""
        self.detail = f"Not found: {response.status}" if detail is None else detail
        super().__init__(response, self.detail)


class AioLXDResponseTypeError(AioLXDException):
    """Exception for AioLXD response type errors."""

    def __init__(self, error: ErrorResponse, detail: Optional[str] = None) -> None:
        """Initialize exception."""
        self.detail = f"Error response: {error.error_code} {error.error} {error}" if detail is None else detail
        self.error = error
        super().__init__(self.detail)


class AioLXDUntrustedCredentials(AioLXDException):
    """Exception for AioLXD untrusted credentials."""

    def __init__(self, detail: Optional[str] = None) -> None:
        """Initialize exception."""
        self.detail = "Untrusted credentials" if detail is None else detail
        super().__init__(self.detail)
