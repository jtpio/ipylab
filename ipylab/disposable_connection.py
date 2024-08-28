# Copyright (c) ipylab contributors.
# Distributed under the terms of the Modified BSD License.

from __future__ import annotations

import uuid
from typing import Generic, TypeVar

from ipywidgets import register
from traitlets import Bool, Unicode

from ipylab.asyncwidget import AsyncWidgetBase

T = TypeVar("T", bound="DisposableConnection")


@register
class DisposableConnection(AsyncWidgetBase, Generic[T]):
    """A connection to a disposable object in the Frontend.

    This defines the 'base' as the disposable object meaning the frontend attribute methods
    are associated directly with the object on the frontend.

    The 'dispose' method will call the dispose method on the frontend object and close

    see: https://lumino.readthedocs.io/en/latest/api/modules/disposable.html

    Subclasses that are inherited with and ID_PREFIX.

    In some cases it may be necessary use the keyword argument `cid` to ensure
    the subclass instance is returned. The class methods `to_cid` and `new_cid`
    will generate an appropriate id.
    """

    ID_PREFIX = ""
    _CLASS_DEFINITIONS: dict[str, type[T]] = {}  # noqa RUF012
    _connections: dict[str, T] = {}  # noqa RUF012
    _model_name = Unicode("DisposableConnectionModel").tag(sync=True)
    cid = Unicode(read_only=True).tag(sync=True)
    _dispose = Bool(read_only=True).tag(sync=True)

    def __init_subclass__(cls, **kwargs) -> None:
        if cls.ID_PREFIX:
            cls._CLASS_DEFINITIONS[cls.ID_PREFIX] = cls  # type: ignore
        super().__init_subclass__(**kwargs)

    def __new__(cls, *, cid: str, **kwgs):
        if cid not in cls._connections:
            if cls.ID_PREFIX and not cid.startswith(cls.ID_PREFIX):
                msg = f"Expected prefix '{cls.ID_PREFIX}' not found for {cid=}"
                raise ValueError(msg)
            # Check if a subclass is registered with 'ID_PREFIX'
            cls_ = cls._CLASS_DEFINITIONS.get(cid.split(":")[0], cls) if ":" in cid else cls
            cls._connections[cid] = super().__new__(cls_, **kwgs)  # type: ignore
        return cls._connections[cid]

    def __str__(self):
        return self.cid

    @classmethod
    def to_cid(cls, *args: str) -> str:
        """Generate an id for the args"""
        return " | ".join([f"{cls.ID_PREFIX}:{args[0].removeprefix(cls.ID_PREFIX).strip(':')}", *args[1:]]).strip(": ")

    @classmethod
    def new_cid(cls, *args):
        return cls.to_cid(str(uuid.uuid4()), *args)

    @classmethod
    def get_instances(cls) -> tuple[T]:
        return tuple(item for item in cls._connections.values() if item.__class__ is cls)  # type: ignore

    def __init__(self, *, cid: str, model_id=None, **kwgs):
        if self._async_widget_base_init_complete:
            return
        self.set_trait("cid", cid)
        super().__init__(model_id=model_id, **kwgs)

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
