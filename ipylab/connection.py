# Copyright (c) ipylab contributors.
# Distributed under the terms of the Modified BSD License.

from __future__ import annotations

import uuid
import weakref
from typing import TYPE_CHECKING, Any, ClassVar

from ipywidgets import Widget, register
from traitlets import Bool, Dict, Unicode

from ipylab.asyncwidget import AsyncWidgetBase, pack

if TYPE_CHECKING:
    from collections.abc import Generator
    from typing import Literal, overload

    from ipylab._compat.typing import Self


@register
class Connection(AsyncWidgetBase):
    """A connection to a single object in the Frontend.

    Connection and subclasses of connection are used extensiviely in ipylab to
    provide a connection between an object in the frontend (Javascript) and the
    backend (Python). Instances of `Connections` are created automatically when
    the transform is set as `Transform.connection`. This option is available whenever
    a transform argument is available in a method call that goes to `schedule_operation`.

    When the `cid` *prefix* matches a subclass `CID_PREFIX`, a new subclass instance will
    be created in place of Connection (on the python side).

    The 'dispose' method will call the dispose method on the frontend object and
    close this object.

    Non-disposable objects are patched with a blank `dispose` method.

    see: https://lumino.readthedocs.io/en/latest/api/modules/disposable.html

    Subclasses that are inherited with and CID_PREFIX.

    If a specific subclass of Connection is required, the transform should be
    specified with the cid from the subclass. Use the keyword argument `cid` to ensure
    the subclass instance is returned. The class methods `to_cid` will generate an
    appropriate id.

    See also `Transform.connection` for further detail about transforms.
    """

    _CLASS_DEFINITIONS: ClassVar[dict[str, type[Self]]] = {}
    _cid_prefix: ClassVar = "ipylab-connection"
    _connections: weakref.WeakValueDictionary[str, Self] = weakref.WeakValueDictionary()
    _model_name = Unicode("ConnectionModel").tag(sync=True)
    cid = Unicode(read_only=True, help="connection id").tag(sync=True)
    id = Unicode("", read_only=True, help="id of the object if it has one").tag(sync=True)
    info = Dict(help="Info to store in the connection")
    _dispose = Bool(read_only=True).tag(sync=True)
    _basename = None

    def __init_subclass__(cls, **kwargs) -> None:
        cls._cid_prefix = "ipylab" + "".join(f"-{c.lower()}" if c.isupper() else c for c in cls.__name__)
        cls._CLASS_DEFINITIONS[cls._cid_prefix] = cls
        super().__init_subclass__(**kwargs)

    def __new__(cls, cid: str, id: str = "", info: dict | None = None, **kwgs):  # noqa: A002
        inst = cls._connections.get(cid)
        if not inst:
            cls = cls._CLASS_DEFINITIONS[cid.split(":", maxsplit=1)[0]]
            cls._connections[cid] = inst = super().__new__(cls, **kwgs)
            inst.set_trait("cid", cid)
        inst.set_trait("id", id or inst.id)
        inst.set_trait("info", info or inst.info)
        return inst

    def __init__(self, *args, cid="", id="", info: dict | None = None, **kwgs):  # noqa: A002, ARG002
        super().__init__(**kwgs)

    def __str__(self):
        return self.cid

    @classmethod
    def to_cid(cls, *args) -> str:
        """Generate an id for the args"""

        args_ = [str(arg.id) if isinstance(arg, Connection) else str(pack(arg)) for arg in args]
        if not args_:
            args_.append(str(uuid.uuid4()))
        arg0 = args_[0].removeprefix(cls._cid_prefix).strip(":")
        return "|".join([f"{cls._cid_prefix}:{arg0}", *args_[1:]]).strip(": ")

    @classmethod
    def get_instances(cls) -> Generator[Self, Any, None]:
        for item in cls._connections.values():
            if item.__class__ is cls:
                yield item  # type: ignore

    def close(self, *, dispose=False):
        """Permanently close the widget.

        dispose: bool
            Whether to dispose of the object at the frontend."""
        if dispose:
            self.set_trait("_dispose", True)
        self._connections.pop(self.cid, None)
        super().close()

    if TYPE_CHECKING:

        @overload
        @classmethod
        def get_existing_connection(cls, *name_or_id: str, quiet: Literal[False]) -> Self: ...
        @overload
        @classmethod
        def get_existing_connection(cls, *name_or_id: str, quiet: bool) -> Self | None: ...
        @overload
        @classmethod
        def get_existing_connection(cls, *name_or_id: str) -> Self: ...

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


Connection._CLASS_DEFINITIONS[Connection._cid_prefix] = Connection  # noqa: SLF001


class ShellConnection(Connection):
    "Provides a connection to a widget loaded in the shell"

    def close(self, *, dispose=None):
        """Permanently close the widget.

        dispose: bool
            Whether to dispose of the object at the frontend.
            If None, dispose will be True if the widget originated from ipylab.
        """
        super().close(dispose=self.id.startswith("IPY_MODEL_") if dispose is None else dispose)

    def activate(self):
        task = self.app.shell.execute_method("activateById", self.id)

        async def activate():
            await task
            return self

        return self.to_task(activate())


class ModelConnection(Connection):
    """A connection to the model of an Ipywidget."""

    def __new__(cls, widget: Widget, **kwgs) -> Self:
        return super().__new__(cls, cid=cls.to_cid(widget), id=pack(widget), **kwgs)
