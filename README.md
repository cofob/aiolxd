# aiolxd

WIP AsyncIO LXD API for Python 3.

## **THIS PROJECT IS NOT READY FOR PRODUCTION USE**

## Example

```python
import asyncio

from aiolxd import LXD


async def main() -> None:
    async with LXD.with_async("https://localhost:8443", cert=("client.crt", "client.key")) as lxd:
        create_task = await lxd.instance.create(
            name="test-instance", source="ubuntu/22.04", type_="virtual-machine"
        )  # Request the creation of an instance
        await create_task.wait()  # Wait for the task to complete

        print(await lxd.instance.get("test-instance"))
        # architecture='x86_64' created_at='2023-02-07T13:05:12.631550731Z'
        # last_used_at='1970-01-01T00:00:00Z' location='none' name='test-instance'
        # profiles=['default'] project='default' restore=None stateful=False
        # status='Stopped' status_code=102 type='virtual-machine' description=''
        # devices={} ephemeral=False config=InstanceConfig(security_nesting=None)

        delete_task = await lxd.instance.delete("test-instance")  # Request the deletion of an instance
        await delete_task.wait()  # Wait for the task to complete


asyncio.run(main())
```

## TODO

- [x] Basic API (instance creation, deletion, etc.)
- [x] Logging
- [ ] Websocket operation events (websocket support exists, but events are not parsed)
- [ ] Tests
- [ ] More API endpoints
