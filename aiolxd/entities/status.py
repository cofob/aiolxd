"""Status schema for /1.0 endpoint."""

from typing import List

from pydantic import BaseModel


class StatusEntity(BaseModel):
    api_extensions: List[str]
    api_status: str
    api_version: str
    auth: str
    public: bool
    auth_methods: List[str]
