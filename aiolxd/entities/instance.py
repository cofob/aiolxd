from pydantic import BaseModel

from .abc import lazy_entity


@lazy_entity
class InstanceEntity(BaseModel):
    architecture: str
