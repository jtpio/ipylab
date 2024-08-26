# Copyright (c) ipylab contributors.
# Distributed under the terms of the Modified BSD License.

from __future__ import annotations

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

    The 'dispose' method will call the dispose method on the frontend object and close.

    see: https://lumino.readthedocs.io/en/latest/api/modules/disposable.html

    Subclasses that are inherited with and ID_PREFIX
    """

    ID_PREFIX = ""
    _CLASS_DEFINITIONS: dict[str, type[T]] = {}  # noqa RUF012
    _connections: dict[str, T] = {}  # noqa RUF012
    _model_name = Unicode("DisposableConnectionModel").tag(sync=True)
    id = Unicode(read_only=True).tag(sync=True)
    _dispose = Bool(read_only=True).tag(sync=True)

    def __init_subclass__(cls, **kwargs) -> None:
        if cls.ID_PREFIX:
            cls._CLASS_DEFINITIONS[cls.ID_PREFIX] = cls  # type: ignore
        super().__init_subclass__(**kwargs)

    def __new__(cls, *, id: str, **kwgs):  # noqa A002
        if id not in cls._connections:
            if cls.ID_PREFIX and not id.startswith(cls.ID_PREFIX):
                msg = f"Expected prefix '{cls.ID_PREFIX}' not found for {id=}"
                raise ValueError(msg)
            # Check if a subclass is registered with 'ID_PREFIX'
            cls_ = cls._CLASS_DEFINITIONS.get(id.split(":")[0], cls) if ":" in id else cls
            cls._connections[id] = super().__new__(cls_, **kwgs)  # type: ignore
        return cls._connections[id]

    def __str__(self):
        return self.id

    @classmethod
    def to_id(cls, name_or_id: str | T) -> str:
        """Generate an id for the given name."""
        if isinstance(name_or_id, DisposableConnection):
            if not isinstance(name_or_id, cls):
                msg = f"{name_or_id} is not a subclass of {cls}"
                raise TypeError(msg)
            return name_or_id.id
        if not cls.ID_PREFIX:
            return name_or_id
        return f"{cls.ID_PREFIX}:{name_or_id.removeprefix(cls.ID_PREFIX).strip(':')}"

    @classmethod
    def get_instances(cls) -> tuple[T]:
        return tuple(item for item in cls._connections.values() if item.__class__ is cls)  # type: ignore

    def __init__(self, *, id: str, model_id=None, **kwgs):  # noqa: A002
        if self._async_widget_base_init_complete:
            return
        self.set_trait("id", id)
        super().__init__(model_id=model_id, **kwgs)

    def close(self):
        self._connections.pop(self.id, None)
        super().close()

    def dispose(self):
        "Dispose of the disposable on the frontend and close."
        self.set_trait("_dispose", True)
        self.close()

    @classmethod
    def get_existing_connection(cls, name_or_id: str | T, *, quiet=False):
        """Get an existing connection.

        quiet: bool
            If the connection does exist:
                * False -> Will raise an error.
                * True -> Will return None.
        """
        id_ = cls.to_id(name_or_id)
        conn = cls._connections.get(id_)
        if not conn and not quiet:
            msg = f"A connection does not exist with id='{id_}'"
            raise ValueError(msg)
        return conn
