from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from .abc import LazyEntity


class InstanceConfig(BaseModel):
    security_nesting: Optional[str] = Field(alias="security.nesting")


class InstanceDevice(BaseModel):
    path: str
    pool: str
    type: str


class InstanceEntity(LazyEntity):
    architecture: str
    created_at: str
    last_used_at: str
    location: str
    name: str
    profiles: List[str]
    project: str
    restore: Optional[str]
    stateful: bool
    status: str
    status_code: int
    type: str
    description: str
    devices: Dict[str, InstanceDevice]
    ephemeral: bool
    config: InstanceConfig


class InstanceSource(BaseModel):
    alias: str
    type: str = Field(default="image")


class InstanceCreateRequest(BaseModel):
    architecture: str = "x86_64"
    type: str = Field(default="container")
    name: str
    source: InstanceSource
