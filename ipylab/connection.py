# Copyright (c) ipylab contributors.
# Distributed under the terms of the Modified BSD License.

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Generic, TypeVar

from ipywidgets import register
from traitlets import Bool, Unicode

from ipylab.asyncwidget import AsyncWidgetBase

if TYPE_CHECKING:
    from asyncio import Task

    from ipylab._compat.typing import Self

T = TypeVar("T", bound="Connection")


@register
class Connection(AsyncWidgetBase, Generic[T]):
    """A connection to an object in the Frontend.

    Instances of `Connections` are created automatically when the transform is set as
    `Transform.connection`.

    When the `cid` *prefix* matches a subclass `CID_PREFIX`, a new subclass instance will
    be created in place of the Connection.

    If a specific subclass of Connection is required, the transform should be
    specified using:

    ```python
    transform = {
        "transform": Transform.connection,
        "cid": CONNECTION_SUBCLASS.new_cid(),
    }
    # or
    transform = {
        "transform": Transform.connection,
        "cid": CONNECTION_SUBCLASS.to_cid(DETAILS),
    }
    ```
    The 'dispose' method will call the dispose method on the frontend object and
    close this object.

    Non-disposable objects are patched with a blank `dispose` method.

    see: https://lumino.readthedocs.io/en/latest/api/modules/disposable.html

    Subclasses that are inherited with and CID_PREFIX.

    In some cases it may be necessary use the keyword argument `cid` to ensure
    the subclass instance is returned. The class methods `to_cid` and `new_cid`
    will generate an appropriate id.
    """

    CID_PREFIX = ""  # Required in subclassess to discriminate when creating.
    _CLASS_DEFINITIONS: dict[str, type[T]] = {}  # noqa RUF012
    _connections: dict[str, T] = {}  # noqa RUF012
    _model_name = Unicode("ConnectionModel").tag(sync=True)
    cid = Unicode(read_only=True, help="connection id").tag(sync=True)
    id = Unicode("", read_only=True, help="id of the object if it has one").tag(sync=True)
    _dispose = Bool(read_only=True).tag(sync=True)
    _basename = None

    def __init_subclass__(cls, **kwargs) -> None:
        if cls.CID_PREFIX:
            cls._CLASS_DEFINITIONS[cls.CID_PREFIX] = cls  # type: ignore
        super().__init_subclass__(**kwargs)

    def __new__(cls, *, cid: str, id: str | None = None, **kwgs):  # noqa: A002, ARG003
        if cid not in cls._connections:
            if cls.CID_PREFIX and not cid.startswith(cls.CID_PREFIX):
                msg = f"Expected prefix '{cls.CID_PREFIX}' not found for {cid=}"
                raise ValueError(msg)
            # Check if a subclass is registered with 'CID_PREFIX'
            cls_ = cls._CLASS_DEFINITIONS.get(cid.split(":")[0], cls) if ":" in cid else cls
            cls._connections[cid] = super().__new__(cls_, **kwgs)  # type: ignore
        return cls._connections[cid]

    def __init__(self, *, cid: str, model_id=None, id: str | None = None, **kwgs):  # noqa: A002
        if self._async_widget_base_init_complete:
            return
        self.set_trait("cid", cid)
        self.set_trait("id", id or "")
        super().__init__(model_id=model_id, **kwgs)

    def __str__(self):
        return self.cid

    @classmethod
    def to_cid(cls, *args: str) -> str:
        """Generate an id for the args"""
        return " | ".join([f"{cls.CID_PREFIX}:{args[0].removeprefix(cls.CID_PREFIX).strip(':')}", *args[1:]]).strip(
            ": "
        )

    @classmethod
    def new_cid(cls, *args):
        return cls.to_cid(str(uuid.uuid4()), *args)

    @classmethod
    def get_instances(cls) -> tuple[T]:
        return tuple(item for item in cls._connections.values() if item.__class__ is cls)  # type: ignore

    def close(self):
        self._connections.pop(self.cid, None)
        super().close()

    def dispose(self):
        "Dispose of the disposable on the frontend and close."
        self.set_trait("_dispose", True)
        self.close()

    @classmethod
    def get_existing_connection(cls, *name_or_id: str, quiet=False):
        """Get an existing connection.

        quiet: bool
            If the connection does exist:
                * False -> Will raise an error.
                * True -> Will return None.
        """
        cid = cls.to_cid(*name_or_id)
        conn = cls._connections.get(cid)
        if not conn and not quiet:
            msg = f"A connection does not exist with id='{cid}'"
            raise ValueError(msg)
        return conn


class MainAreaConnection(Connection):
    CID_PREFIX = "ipylab MainArea"

    def activate(self) -> Task[Self]:
        self._check_closed()

        async def activate_():
            self.app.shell.execute_method("activateById", self.id)
            return self

        return self.to_task(activate_())
