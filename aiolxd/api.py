from typing import Any

from aiohttp import ClientSession

from .raw import RawLXDCaller


class LXD:
    def __init__(self, api_endpoint: str, session: ClientSession | None = None, raw_params: dict[str, Any] = {}):
        self.api_endpoint = api_endpoint
        self.session = session or ClientSession()
        self.raw = RawLXDCaller(self.session, api_endpoint, True, **raw_params)

    async def close(self) -> None:
        await self.session.close()

    async def __aenter__(self) -> "LXD":
        return self

    async def __aexit__(self, _exc_type: Any, _exc: Any, _tb: Any) -> None:
        await self.close()

    async def containers(self) -> Any:
        return await self.raw.containers.get()
