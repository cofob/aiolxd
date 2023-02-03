from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Union


class BaseResponse:
    type_: str
    metadata: Optional[Union[Dict[str, Any], List[Any]]]


@dataclass
class SyncResponse(BaseResponse):
    # Duplication is required for dataclasses to work
    type_: str
    metadata: Optional[Union[Dict[str, Any], List[Any]]]

    status: str
    status_code: "StatusCode"


@dataclass
class AsyncResponse(BaseResponse):
    type_: str
    metadata: Optional[Union[Dict[str, Any], List[Any]]]

    status: str
    status_code: "StatusCode"
    operation: str


@dataclass
class ErrorResponse(BaseResponse):
    type_: str
    metadata: Optional[Union[Dict[str, Any], List[Any]]]

    error: str
    error_code: "StatusCode"


class StatusCode(Enum):
    OPERTAINON_CREATED = 100
    STARTED = 101
    STOPPED = 102
    RUNNING = 103
    CANCELING = 104
    PENDING = 105
    STARTING = 106
    STOPPING = 107
    ABORTING = 108
    FREEZING = 109
    FROZEN = 110
    THAWED = 111
    ERROR = 112
    READY = 113
    SUCCESS = 200
    FAILURE = 400
    CANCELED = 401
    NOT_FOUND = 404
