import logging
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

if TYPE_CHECKING:
    from ..transport import AbstractTransport


logger = logging.getLogger(__name__)


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


class BaseResponse:
    type_: str
    metadata: Optional[Union[Dict[str, Any], List[Any]]]

    def get_internal_status(self) -> StatusCode:
        """Get the internal status of the response."""
        if not isinstance(self.metadata, dict):
            raise ValueError("Invalid metadata type")
        if "status" not in self.metadata:
            raise ValueError("Metadata has no status")
        return StatusCode(self.metadata["status"])


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
    metadata: Dict[str, Any]

    status: str
    status_code: StatusCode
    operation: str

    transport: "AbstractTransport"

    async def wait(self) -> SyncResponse:
        """Wait for an async operation to complete."""
        logger.debug("Waiting for operation %s", self.operation)
        resp = await self.transport.get(f"{self.operation}/wait")
        if not isinstance(resp, SyncResponse):
            raise ValueError("Invalid response type")
        return resp


@dataclass
class ErrorResponse(BaseResponse):
    type_: str
    metadata: Optional[Union[Dict[str, Any], List[Any]]]

    error: str
    error_code: "StatusCode"
