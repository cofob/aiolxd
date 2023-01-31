from typing import Any, Literal

from pydantic import BaseModel, Field


class RawResponseSchema(BaseModel):
    """Base schema for raw responses."""

    type_: Literal["sync"] | Literal["async"] | Literal["error"] = Field(
        alias="type", default="sync", regex="sync|async|error"
    )
    status: str | None = Field(...)
    status_code: int | None = Field(default=200, ge=100, le=599)
    operation: str | None = None
    error_code: int | None = None
    error: str | None = None
    metadata: dict[str, Any] | None = None
