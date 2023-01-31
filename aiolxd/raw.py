"""Low-level API for LXD."""

from typing import Any

from aiohttp import ClientResponse, ClientSession


class RawLXDCaller:
    """A class to call and construct paths for the LXD API.

    This class is used to construct paths for the LXD API. It is
    constructed with a session and a path, and can be called to
    perform a GET request on that path. It can also be used to
    construct a new path by calling methods on it, or by using
    the slash method to add a slash to the path.

    The path is constructed by calling methods on the object, or
    by using the slash method. For example, to get the list of
    containers, you would do:

    >>> await lxd.containers()

    Equals to:

    >>> await lxd.slash("containers")

    Or:

    >>> await lxd.slash("containers").get()

    Slash method can be used to add a slash to the path:

    >>> await lxd.slash("containers").slash().get()

    Or to add a complex or dynamic path:

    >>> await lxd.containers.slash(container).get()

    You can also call methods multiple times to add multiple
    paths:

    >>> await lxd.containers.slash(container).files.slash("root").get()

    To call specific HTTP methods, you can use the post, put,
    delete, patch, and get methods. These methods take the same
    arguments as the aiohttp session methods.

    >>> await lxd.containers.post()
    >>> await lxd.containers.put()
    >>> await lxd.containers.delete()
    >>> await lxd.containers.patch()
    >>> await lxd.containers.get()

    RawLXDCaller never mutates, it always returns a new object. So you can
    do things like:

    >>> path1 = lxd.containers
    >>> path2 = path1.slash("foo")
    >>> path3 = path1.slash("bar")
    >>> assert path1, path2, path3 == "/1.0/containers", "/1.0/containers/foo", "/1.0/containers/bar"
    """

    def __init__(self, session: ClientSession, path: str, initial: bool = True, **kwargs: Any) -> None:
        """Create a new RawLXDCaller.

        kwargs are passed to the aiohttp session.

        Example:

        >>> lxd = RawLXDCaller(session, "https://localhost:8443")
        >>> await lxd.containers()
        """
        self._session = session
        if initial:
            if not path.startswith("http"):
                raise ValueError("Path must start with http")
            if not path.endswith("/1.0"):
                path += "/1.0"
        self._path = path
        self._kwargs = kwargs

    def _construct(self, path: str) -> "RawLXDCaller":
        """Construct a new RawLXDCaller."""
        return RawLXDCaller(self._session, path, initial=False, **self._kwargs)

    def slash(self, path: str | None = None) -> "RawLXDCaller":
        """Add a slash to the path."""
        if path is None:
            return self._construct(self._path + "/")
        return self._construct(self._path + "/" + path)

    def path(self, path: str) -> "RawLXDCaller":
        """Add a path to the path."""
        return self._construct(self._path + "/" + path)

    def __getattr__(self, name: str) -> "RawLXDCaller":
        """Get an attribute from the path."""
        if name.startswith("__") and name.endswith("__"):
            # Python internal stuff
            raise AttributeError
        return self._construct(self._path + "/" + name)

    def __repr__(self) -> str:
        """Return a representation of the object."""
        return f"RawLXDCaller({self._path!r})"

    def __str__(self) -> str:
        """Return a string representation of the object."""
        return self._path

    def __eq__(self, other: Any) -> bool:
        """Return whether the object is equal to another object."""
        if not isinstance(other, RawLXDCaller):
            return False
        return self._path == other._path

    async def __call__(self, *args: Any, **kwds: Any) -> ClientResponse:
        """Call the path.

        Args and kwargs are passed to the aiohttp session.
        """
        return await self._session.get(self._path, *args, **self._kwargs, **kwds)

    async def post(self, *args: Any, **kwds: Any) -> ClientResponse:
        """Post to the path.

        Args and kwargs are passed to the aiohttp session.
        """
        return await self._session.post(self._path, *args, **self._kwargs, **kwds)

    async def put(self, *args: Any, **kwds: Any) -> ClientResponse:
        """Put to the path.

        Args and kwargs are passed to the aiohttp session.
        """
        return await self._session.put(self._path, *args, **self._kwargs, **kwds)

    async def delete(self, *args: Any, **kwds: Any) -> ClientResponse:
        """Delete to the path.

        Args and kwargs are passed to the aiohttp session.
        """
        return await self._session.delete(self._path, *args, **self._kwargs, **kwds)

    async def patch(self, *args: Any, **kwds: Any) -> ClientResponse:
        """Patch to the path.

        Args and kwargs are passed to the aiohttp session.
        """
        return await self._session.patch(self._path, *args, **self._kwargs, **kwds)

    async def get(self, *args: Any, **kwds: Any) -> ClientResponse:
        """Get to the path.

        Args and kwargs are passed to the aiohttp session.

        This is the same as calling the object, but is provided for
        consistency with the other methods.
        """
        return await self._session.get(self._path, *args, **self._kwargs, **kwds)
